"""
Views для обробки замовлень, оплати та розсилки
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from apps.cart.cart import Cart
from decimal import Decimal
from .models import Newsletter, Order, OrderItem, PendingPayment
from .novaposhta import NovaPoshtaAPI
from .validators import validate_order_data
import hashlib
import base64
import json
import logging

logger = logging.getLogger(__name__)

MINIMUM_WHOLESALE_ORDER = Decimal('5000.00')

# Отримуємо ключі з налаштувань, з fallback на sandbox для розробки
LIQPAY_PUBLIC_KEY = getattr(settings, 'LIQPAY_PUBLIC_KEY', 'sandbox_i69925457912')
LIQPAY_PRIVATE_KEY = getattr(settings, 'LIQPAY_PRIVATE_KEY', 'sandbox_d7fYUF83CUeVdBqHyEeYbjNM65B77RcjnWAIVkUm')


def order_create(request):
    """Створення замовлення"""
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, 'Ваш кошик порожній')
        return redirect('cart:detail')
    
    total_price = cart.get_total_price()
    is_wholesale_user = (
        request.user.is_authenticated and 
        not request.user.is_staff and 
        not request.user.is_superuser
    )
    
    if is_wholesale_user and total_price < MINIMUM_WHOLESALE_ORDER:
        messages.error(
            request, 
            f'Мінімальна сума замовлення для оптових клієнтів становить {MINIMUM_WHOLESALE_ORDER} грн. '
            f'Ваша поточна сума: {total_price} грн. '
            'Будь ласка, додайте ще товарів або вийдіть з особистого кабінету для замовлення без обмежень.'
        )
        return redirect('cart:detail')
    
    if request.method == 'POST':
        if is_wholesale_user and total_price < MINIMUM_WHOLESALE_ORDER:
            messages.error(
                request, 
                f'Мінімальна сума замовлення для оптових клієнтів становить {MINIMUM_WHOLESALE_ORDER} грн.'
            )
            return redirect('cart:detail')
        
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        delivery_method = request.POST.get('delivery_method', '')
        delivery_city = request.POST.get('delivery_city', '').strip()
        delivery_address = request.POST.get('delivery_address', '').strip()
        
        np_city_ref = request.POST.get('np_city_ref', '').strip()
        np_warehouse_ref = request.POST.get('np_warehouse_ref', '').strip()
        delivery_type = request.POST.get('delivery_type', '').strip()
        
        payment_method = request.POST.get('payment_method', '')
        notes = request.POST.get('notes', '').strip()
        
        if delivery_method == 'pickup':
            delivery_city = 'Монастирище'
            if not delivery_address:
                delivery_address = 'Україна, Черкаська область, м.Монастирище, вул. Соборна 126Д'
        
        # Валідація даних форми
        is_valid, error_message = validate_order_data({
            'first_name': first_name,
            'last_name': last_name,
            'middle_name': middle_name,
            'email': email,
            'phone': phone,
            'delivery_method': delivery_method,
            'payment_method': payment_method,
        })
        
        if not is_valid:
            messages.error(request, error_message)
            context = {
                'cart': cart,
                'user': request.user,
                'form_data': request.POST
            }
            return render(request, 'orders/create.html', context)
        
        if not delivery_address:
            messages.error(request, "Будь ласка, вкажіть адресу доставки")
            context = {
                'cart': cart,
                'user': request.user,
                'form_data': request.POST
            }
            return render(request, 'orders/create.html', context)
        
        try:
            logger.info(f"Creating order - User: {request.user.id if request.user.is_authenticated else 'Guest'}, Total: {total_price}")
            
            # БЕЗПЕКА: Перераховуємо ціни на серверній стороні замість довіри сесії
            recalculated_subtotal = Decimal('0')
            order_items_data = []
            
            for item in cart:
                product = item['product']
                quantity = item['quantity']
                
                # Перевірка наявності товару
                if product.stock < quantity:
                    raise ValueError(f'Недостатньо товару "{product.name}" на складі (доступно: {product.stock})')
                
                # КРИТИЧНО: Отримуємо ціну з БД, а не з сесії
                actual_price = product.get_price_for_user(
                    request.user if request.user.is_authenticated and not request.user.is_staff and not request.user.is_superuser else None,
                    quantity
                )
                
                item_total = Decimal(str(actual_price)) * quantity
                recalculated_subtotal += item_total
                
                order_items_data.append({
                    'product': product,
                    'quantity': quantity,
                    'price': actual_price
                })
            
            # Застосовуємо знижку промокоду якщо є
            discount = Decimal('0')
            if 'promo_discount' in request.session and 'promo_id' in request.session:
                from apps.promotions.models import PromoCode
                try:
                    promo = PromoCode.objects.get(id=request.session['promo_id'])
                    is_valid, _ = promo.is_valid()
                    if is_valid:
                        # ВАЖЛИВО: передаємо Decimal, а не float
                        discount_amount, _ = promo.apply_discount(recalculated_subtotal)
                        discount = Decimal(str(discount_amount))
                        
                        # Збільшуємо лічильник використань
                        promo.used_count += 1
                        promo.save(update_fields=['used_count'])
                        logger.info(f"Promo code {promo.code} applied: {discount}")
                except PromoCode.DoesNotExist:
                    logger.warning(f"Promo code {request.session.get('promo_id')} not found")
                    discount = Decimal('0')
                except (ValueError, TypeError) as e:
                    logger.error(f"Promo code calculation error: {e}")
                    discount = Decimal('0')
            
            final_total = recalculated_subtotal - discount
            
            # Перевірка на від'ємну суму (захист від маніпуляцій)
            if final_total < 0:
                raise ValueError('Некоректна сума замовлення')
            
            logger.info(f"Creating order with data: first_name={first_name}, last_name={last_name}, email={email}, payment={payment_method}")
            
            # КРИТИЧНА ЗМІНА: Для LiqPay НЕ створюємо замовлення відразу
            if payment_method == 'liqpay':
                serializable_items = []
                for item_data in order_items_data:
                    serializable_items.append({
                        'product_id': item_data['product'].id,
                        'quantity': item_data['quantity'],
                        'price': str(item_data['price'])
                    })
                
                order_data_dict = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'middle_name': middle_name,
                    'email': email,
                    'phone': phone,
                    'delivery_method': delivery_method,
                    'delivery_city': delivery_city or 'Не вказано',
                    'delivery_address': delivery_address,
                    'np_city_ref': np_city_ref,
                    'np_warehouse_ref': np_warehouse_ref,
                    'delivery_type': delivery_type,
                    'payment_method': payment_method,
                    'subtotal': str(recalculated_subtotal),
                    'discount': str(discount),
                    'total': str(final_total),
                    'notes': notes,
                    'order_items': serializable_items,
                    'user_id': request.user.id if request.user.is_authenticated else None
                }
                
                import time
                transaction_ref = f"temp_{int(time.time() * 1000)}"
                
                PendingPayment.objects.create(
                    transaction_ref=transaction_ref,
                    order_data=order_data_dict
                )
                
                request.session['pending_transaction_ref'] = transaction_ref
                
                logger.info(f"Pending LiqPay payment created: {transaction_ref}")
                return redirect('orders:liqpay_payment_pending')
            
            # Для готівкової оплати - створюємо замовлення як раніше
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                email=email,
                phone=phone,
                delivery_method=delivery_method,
                delivery_city=delivery_city or 'Не вказано',
                delivery_address=delivery_address,
                np_city_ref=np_city_ref,
                np_warehouse_ref=np_warehouse_ref,
                delivery_type=delivery_type,
                payment_method=payment_method,
                subtotal=recalculated_subtotal,
                discount=discount,
                total=final_total,
                notes=notes
            )
            
            logger.info(f"Order #{order.order_number} created successfully (ID: {order.id})")
            
            # Створюємо items з перерахованими цінами
            for item_data in order_items_data:
                OrderItem.objects.create(
                    order=order,
                    product=item_data['product'],
                    quantity=item_data['quantity'],
                    price=item_data['price']
                )
            
            logger.info(f"Order items created for order #{order.order_number}")
            
            # Для готівкової оплати - очищаємо кошик відразу
            cart.clear()
            request.session['completed_order_id'] = order.id
            logger.info(f"Order #{order.order_number} completed (cash payment)")
            return redirect('orders:success')
            
        except ValueError as e:
            logger.warning(f"Order validation error: {e}")
            messages.error(request, str(e))
            context = {
                'cart': cart,
                'user': request.user,
                'form_data': request.POST
            }
            return render(request, 'orders/create.html', context)
        except Exception as e:
            logger.exception(f"Order creation error: {type(e).__name__}: {e}")
            messages.error(request, f'Помилка при створенні замовлення: {str(e)}. Будь ласка, спробуйте пізніше.')
            context = {
                'cart': cart,
                'user': request.user,
                'form_data': request.POST
            }
            return render(request, 'orders/create.html', context)
    
    return render(request, 'orders/create.html', {
        'cart': cart,
        'user': request.user
    })


def order_success(request):
    """Сторінка успішного замовлення"""
    order_id = request.session.pop('completed_order_id', None)
    payment_status = request.session.pop('payment_status', None)
    payment_error = request.session.pop('payment_error', None)
    order = None
    
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found in success page")
            pass
    
    return render(request, 'orders/success.html', {
        'order': order,
        'payment_status': payment_status,
        'payment_error': payment_error
    })


@require_GET
def np_search_cities(request):
    """API пошук міст Нової Пошти"""
    query = request.GET.get('query', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'success': False, 'cities': []})
    
    api = NovaPoshtaAPI()
    cities = api.search_cities(query)
    
    return JsonResponse({
        'success': True,
        'cities': cities
    })


@require_GET
def np_get_warehouses(request):
    """API отримання відділень Нової Пошти"""
    city_ref = request.GET.get('city_ref', '').strip()
    warehouse_type = request.GET.get('type', '').strip()
    
    if not city_ref:
        return JsonResponse({'success': False, 'warehouses': []})
    
    api = NovaPoshtaAPI()
    warehouses = api.get_warehouses(city_ref, warehouse_type)
    
    return JsonResponse({
        'success': True,
        'warehouses': warehouses
    })


def liqpay_payment_pending(request):
    """Сторінка оплати через LiqPay (до створення замовлення)"""
    transaction_ref = request.session.get('pending_transaction_ref')
    
    if not transaction_ref:
        messages.error(request, 'Дані замовлення не знайдено. Будь ласка, оформіть замовлення заново.')
        return redirect('orders:create')
    
    try:
        pending_payment = PendingPayment.objects.get(transaction_ref=transaction_ref)
    except PendingPayment.DoesNotExist:
        messages.error(request, 'Дані замовлення не знайдено. Будь ласка, оформіть замовлення заново.')
        return redirect('orders:create')
    
    if pending_payment.is_processed:
        messages.info(request, 'Це замовлення вже оброблено.')
        if pending_payment.created_order:
            request.session['completed_order_id'] = pending_payment.created_order.id
        return redirect('orders:success')
    
    order_data = pending_payment.order_data
    
    protocol = 'https' if request.is_secure() or 'render.com' in request.get_host() else 'http'
    host = request.get_host()
    callback_url = f'{protocol}://{host}/orders/liqpay-callback/'
    result_url = f'{protocol}://{host}/orders/success/'
    
    logger.info(f"LiqPay payment initiated for pending order, callback: {callback_url}")
    
    data_dict = {
        'version': 3,
        'public_key': LIQPAY_PUBLIC_KEY,
        'action': 'pay',
        'amount': order_data['total'],
        'currency': 'UAH',
        'description': f'Оплата замовлення',
        'order_id': transaction_ref,
        'result_url': result_url,
        'server_url': callback_url
    }
    
    data_json = json.dumps(data_dict)
    data = base64.b64encode(data_json.encode('utf-8')).decode('utf-8')
    
    sign_string = LIQPAY_PRIVATE_KEY + data + LIQPAY_PRIVATE_KEY
    signature = base64.b64encode(hashlib.sha1(sign_string.encode('utf-8')).digest()).decode('utf-8')
    
    logger.info(f"LiqPay data generated for pending order")
    
    class PendingOrder:
        def __init__(self, data):
            self.order_number = "очікується"
            self.total = data['total']
            self.email = data['email']
            self.phone = data['phone']
            self.first_name = data['first_name']
            self.last_name = data['last_name']
            self.middle_name = data.get('middle_name', '')
            self.delivery_method = data['delivery_method']
            
        def get_customer_name(self):
            if self.middle_name:
                return f"{self.first_name} {self.last_name} {self.middle_name}"
            return f"{self.first_name} {self.last_name}"
            
        def get_delivery_method_display(self):
            methods = {
                'nova_poshta': 'Нова Пошта',
                'ukrposhta': 'Укрпошта',
                'pickup': 'Самовивіз'
            }
            return methods.get(self.delivery_method, self.delivery_method)
    
    return render(request, 'orders/liqpay_payment.html', {
        'order': PendingOrder(order_data),
        'data': data,
        'signature': signature,
        'public_key': LIQPAY_PUBLIC_KEY
    })


def liqpay_payment(request, order_id):
    """Сторінка оплати через LiqPay (для існуючого замовлення)"""
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, 'Замовлення не знайдено')
        return redirect('core:home')
    
    if order.is_paid:
        messages.info(request, 'Це замовлення вже оплачено')
        return redirect('orders:success')
    
    # Формуємо правильний URL для callback
    protocol = 'https' if request.is_secure() or 'render.com' in request.get_host() else 'http'
    host = request.get_host()
    callback_url = f'{protocol}://{host}/orders/liqpay-callback/'
    result_url = f'{protocol}://{host}/orders/success/'
    
    logger.info(f"LiqPay payment initiated for order #{order.order_number}, callback: {callback_url}")
    
    data_dict = {
        'version': 3,
        'public_key': LIQPAY_PUBLIC_KEY,
        'action': 'pay',
        'amount': str(order.total),
        'currency': 'UAH',
        'description': f'Оплата замовлення #{order.order_number}',
        'order_id': str(order.id),
        'result_url': result_url,
        'server_url': callback_url
    }
    
    data_json = json.dumps(data_dict)
    data = base64.b64encode(data_json.encode('utf-8')).decode('utf-8')
    
    sign_string = LIQPAY_PRIVATE_KEY + data + LIQPAY_PRIVATE_KEY
    signature = base64.b64encode(hashlib.sha1(sign_string.encode('utf-8')).digest()).decode('utf-8')
    
    logger.info(f"LiqPay data generated for order #{order.order_number}")
    
    return render(request, 'orders/liqpay_payment.html', {
        'order': order,
        'data': data,
        'signature': signature,
        'public_key': LIQPAY_PUBLIC_KEY
    })


@csrf_exempt
@require_POST
def liqpay_callback(request):
    """Callback для обробки результату оплати LiqPay"""
    data = request.POST.get('data')
    signature = request.POST.get('signature')
    
    if not data or not signature:
        logger.warning('LiqPay callback: missing data or signature')
        return JsonResponse({'success': False, 'error': 'Missing data'})
    
    # Перевірка підпису
    sign_string = LIQPAY_PRIVATE_KEY + data + LIQPAY_PRIVATE_KEY
    expected_signature = base64.b64encode(hashlib.sha1(sign_string.encode('utf-8')).digest()).decode('utf-8')
    
    if signature != expected_signature:
        logger.error('LiqPay callback: invalid signature')
        return JsonResponse({'success': False, 'error': 'Invalid signature'})
    
    try:
        data_decoded = base64.b64decode(data).decode('utf-8')
        payment_data = json.loads(data_decoded)
        
        order_id = payment_data.get('order_id')
        status = payment_data.get('status')
        transaction_id = payment_data.get('transaction_id', '')
        
        if not order_id:
            logger.error('LiqPay callback: missing order_id')
            return JsonResponse({'success': False, 'error': 'Missing order_id'})
        
        logger.info(f'LiqPay callback: order_id={order_id}, status={status}, transaction={transaction_id}')
        
        if str(order_id).startswith('temp_'):
            try:
                pending_payment = PendingPayment.objects.select_for_update().get(
                    transaction_ref=order_id,
                    is_processed=False
                )
            except PendingPayment.DoesNotExist:
                logger.warning(f'LiqPay callback: pending payment {order_id} already processed or not found')
                return JsonResponse({'success': True, 'message': 'Already processed'})
            
            if status == 'success':
                order_data = pending_payment.order_data
                
                from apps.products.models import Product
                order_items_data = []
                for item_data in order_data.get('order_items', []):
                    try:
                        product = Product.objects.get(id=item_data['product_id'])
                        order_items_data.append({
                            'product': product,
                            'quantity': item_data['quantity'],
                            'price': Decimal(str(item_data['price']))
                        })
                    except Product.DoesNotExist:
                        logger.error(f"Product {item_data['product_id']} not found")
                        continue
                
                if not order_items_data:
                    logger.error('LiqPay callback: no valid products found')
                    return JsonResponse({'success': False, 'error': 'No valid products'})
                
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = None
                if order_data.get('user_id'):
                    try:
                        user = User.objects.get(id=order_data['user_id'])
                    except User.DoesNotExist:
                        pass
                
                order = Order.objects.create(
                    user=user,
                    first_name=order_data['first_name'],
                    last_name=order_data['last_name'],
                    middle_name=order_data.get('middle_name', ''),
                    email=order_data['email'],
                    phone=order_data['phone'],
                    delivery_method=order_data['delivery_method'],
                    delivery_city=order_data['delivery_city'],
                    delivery_address=order_data['delivery_address'],
                    np_city_ref=order_data.get('np_city_ref', ''),
                    np_warehouse_ref=order_data.get('np_warehouse_ref', ''),
                    delivery_type=order_data.get('delivery_type', ''),
                    payment_method=order_data['payment_method'],
                    subtotal=Decimal(order_data['subtotal']),
                    discount=Decimal(order_data['discount']),
                    total=Decimal(order_data['total']),
                    notes=order_data.get('notes', ''),
                    is_paid=True,
                    payment_date=timezone.now(),
                    status='confirmed'
                )
                
                for item_data in order_items_data:
                    OrderItem.objects.create(
                        order=order,
                        product=item_data['product'],
                        quantity=item_data['quantity'],
                        price=item_data['price']
                    )
                
                pending_payment.is_processed = True
                pending_payment.created_order = order
                pending_payment.save(update_fields=['is_processed', 'created_order', 'updated_at'])
                
                logger.info(f'✅ Order #{order.order_number} CREATED and PAID (transaction: {transaction_id})')
                
                cart = Cart(request)
                cart.clear()
                
                if 'pending_transaction_ref' in request.session:
                    del request.session['pending_transaction_ref']
                request.session['completed_order_id'] = order.id
                request.session['payment_status'] = 'success'
                
                return JsonResponse({'success': True})
            else:
                pending_payment.is_processed = True
                pending_payment.save(update_fields=['is_processed', 'updated_at'])
                
                logger.warning(f'❌ Pending order payment FAILED: status={status}')
                request.session['payment_status'] = 'failed'
                request.session['payment_error'] = status
                return JsonResponse({'success': False, 'status': status, 'message': 'Payment not successful'})
        else:
            # Це існуюче замовлення
            order = Order.objects.get(id=order_id)
            
            # Захист від повторної обробки платежу
            if order.is_paid:
                logger.info(f'Order #{order.order_number} already paid, skipping')
                return JsonResponse({'success': True, 'message': 'Already processed'})
            
            if status == 'success':
                order.is_paid = True
                order.payment_date = timezone.now()
                order.status = 'confirmed'
                order.save(update_fields=['is_paid', 'payment_date', 'status'])
                
                logger.info(f'✅ Order #{order.order_number} PAID successfully at {order.payment_date.strftime("%Y-%m-%d %H:%M:%S")} (transaction: {transaction_id})')
                
                # Очищаємо кошик ТІЛЬКИ після успішної оплати
                cart = Cart(request)
                cart.clear()
                
                request.session['completed_order_id'] = order.id
                request.session['payment_status'] = 'success'
                
                return JsonResponse({'success': True})
            else:
                # Оплата не пройшла - логуємо статус
                logger.warning(f'❌ Order #{order.order_number} payment FAILED: status={status}')
                request.session['payment_status'] = 'failed'
                request.session['payment_error'] = status
                return JsonResponse({'success': False, 'status': status, 'message': 'Payment not successful'})
            
    except Order.DoesNotExist:
        logger.error(f'LiqPay callback: order {order_id} not found')
        return JsonResponse({'success': False, 'error': 'Order not found'})
    except json.JSONDecodeError as e:
        logger.error(f'LiqPay callback: invalid JSON data - {e}')
        return JsonResponse({'success': False, 'error': 'Invalid data format'})
    except Exception as e:
        logger.exception(f'LiqPay callback error: {e}')
        return JsonResponse({'success': False, 'error': 'Internal error'})


@require_POST
def newsletter_subscribe(request):
    """Підписка на розсилку"""
    try:
        email = request.POST.get('email', '').strip().lower()
        name = request.POST.get('name', '').strip()
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email обов\'язковий'
            })
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if User.objects.filter(email__iexact=email, is_staff=True).exists():
            return JsonResponse({
                'success': False,
                'message': 'Некоректна email адреса'
            })
        
        if User.objects.filter(email__iexact=email, is_superuser=True).exists():
            return JsonResponse({
                'success': False,
                'message': 'Некоректна email адреса'
            })
        
        newsletter, created = Newsletter.objects.get_or_create(
            email=email,
            defaults={'name': name, 'is_active': True}
        )
        
        if not created:
            newsletter.is_active = True
            newsletter.save(update_fields=['is_active'])
        
        return JsonResponse({
            'success': True,
            'message': 'Дякуємо! Ви успішно підписалися на розсилку.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Помилка при підписці. Спробуйте пізніше.'
        })
