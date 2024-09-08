from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, date, time, timedelta
from .models import Product, Cart, Sales, Sale_items
from .forms import ProductForm
from utils.util_functions import parse_datetime, filter_items, admin_required
import pytz


# datetime format
format_datetime = "%Y-%m-%d %H:%M:%S.%f"

def format_num(num, commas=False):
    formatted_num = int(num) if num == int(num) else num
    return '{:,.2f}'.format(formatted_num) if commas else formatted_num

# dashboard page
@never_cache
@login_required
def dashboard_page(request):
    def month_firstday(any_date):
        return any_date.replace(day=1)

    def month_lastday(any_date):
        next_month = any_date.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)
    
    def count_sales(startdate, enddate):
        get_sales = Sales.objects.filter(Q(saledate__range=(startdate, enddate)))
        return sum(item.amount for item in get_sales)

    count_products, count_empty, count_expiry = 0, 0, 0
    today_date = date.today()

    previous_days = [(today_date - timedelta(days=i)) for i in range(1, 5)]

    products = Product.objects.exclude(deleted=True)
    for product in products:
        if product.expiry is None or product.expiry >= today_date:
            count_products += 1
        if product.qty <= 10:
            count_empty += 1
        if product.expiry is not None and product.expiry <= today_date + timedelta(days=7):
            count_expiry += 1

    today_range = (datetime.combine(today_date, time.min), datetime.combine(today_date, time.max))
    previous_day_ranges = [
        (datetime.combine(day, time.min), datetime.combine(day, time.max)) for day in previous_days
    ]

    current_month_range = (
        datetime.combine(month_firstday(today_date), time.min),
        datetime.combine(month_lastday(today_date), time.max)
    )

    previous_months = [month_firstday(today_date.replace(day=1) - timedelta(days=i * 30)) for i in range(1, 5)]
    previous_month_ranges = [
        (
            datetime.combine(month_firstday(month), time.min),
            datetime.combine(month_lastday(month), time.max)
        ) for month in previous_months
    ]

    today_sales = count_sales(*today_range)
    day_sales = [count_sales(*day_range) for day_range in previous_day_ranges]
    month_sales = count_sales(*current_month_range)
    previous_month_sales = [count_sales(*month_range) for month_range in previous_month_ranges]

    context = {
        'count_products': f"{count_products:,.0f}" if count_products > 9 else f"0{count_products}",
        'count_empty': f"{count_empty:,.0f}" if count_empty > 9 else f"0{count_empty}",
        'count_expiry': f"{count_expiry:,.0f}" if count_expiry > 9 else f"0{count_expiry}",
        'today_sales': f"{today_sales:,.2f} TZS",
        'day1_sales': f"{day_sales[0]:,.2f} TZS",
        'day2_sales': f"{day_sales[1]:,.2f} TZS",
        'day3_sales': f"{day_sales[2]:,.2f} TZS",
        'day4_sales': f"{day_sales[3]:,.2f} TZS",
        'month_sales': f"{month_sales:,.2f} TZS",
        'month1_sales': f"{previous_month_sales[0]:,.2f} TZS",
        'month2_sales': f"{previous_month_sales[1]:,.2f} TZS",
        'month3_sales': f"{previous_month_sales[2]:,.2f} TZS",
        'month4_sales': f"{previous_month_sales[3]:,.2f} TZS",
        'day2': previous_days[1].strftime('%d-%b-%Y'),
        'day3': previous_days[2].strftime('%d-%b-%Y'),
        'day4': previous_days[3].strftime('%d-%b-%Y'),
        'month2': previous_months[1].strftime('%b-%Y'),
        'month3': previous_months[2].strftime('%b-%Y'),
        'month4': previous_months[3].strftime('%b-%Y')
    }
    
    return render(request, 'shop/dashboard.html', context)

# inventory page
@never_cache
@login_required
@admin_required()
def inventory_page(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        queryset = Product.objects.exclude(deleted=True)

        # Date range filtering
        reg_start = parse_datetime(request.POST.get('start_reg'), format_datetime, to_utc=True)
        reg_end = parse_datetime(request.POST.get('end_reg'), format_datetime, to_utc=True)
        edit_start = parse_datetime(request.POST.get('start_edit'), format_datetime, to_utc=True)
        edit_end = parse_datetime(request.POST.get('end_edit'), format_datetime, to_utc=True)
        exp_start = parse_datetime(request.POST.get('start_exp'), format_datetime, to_date=True)
        exp_end = parse_datetime(request.POST.get('end_exp'), format_datetime, to_date=True)
        date_range_filters = Q()

        if reg_start and reg_end:
            date_range_filters |= Q(regdate__range=(reg_start, reg_end))
        else:
            if reg_start:
                date_range_filters |= Q(regdate__gte=reg_start)
            elif reg_end:
                date_range_filters |= Q(regdate__lte=reg_end)

        if edit_start and edit_end:
            date_range_filters |= Q(last_edit__range=(edit_start, edit_end))
        else:
            if edit_start:
                date_range_filters |= Q(last_edit__gte=edit_start)
            elif edit_end:
                date_range_filters |= Q(last_edit__lte=edit_end)

        if exp_start and exp_end:
            date_range_filters |= Q(expiry__range=(exp_start, exp_end))
        else:
            if exp_start:
                date_range_filters |= Q(expiry__gte=exp_start)
            elif exp_end:
                date_range_filters |= Q(expiry__lte=exp_end)

        if date_range_filters:
            queryset = queryset.filter(date_range_filters)

        # Base data from queryset
        base_data = []
        for product in queryset:
            product_object = {
                'id': product.id,
                'regdate': product.regdate,
                'lastedit': product.lastEdited,
                'names': product.names,
                'qty': product.qty,
                'price': product.price,
                'expiry': product.expiry,
                'exp_status': 1 if product.expiry is not None and product.expiry <= date.today() else 0,
                'info': reverse('product_details', kwargs={'product_id': int(product.id)})
            }
            base_data.append(product_object)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'regdate',
            2: 'lastedit',
            3: 'names',
            4: 'qty',
            5: 'price',
            6: 'expiry'
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'names')
        def none_safe_sort(item):
            value = item.get(order_column_name)
            return (value is None, value)
        if order_dir == 'asc':
            base_data = sorted(base_data, key=none_safe_sort, reverse=False)
        else:
            base_data = sorted(base_data, key=none_safe_sort, reverse=True)

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '').strip()
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    base_data = [item for item in base_data if filter_items(column_field, column_search, item, ('qty', 'price'))]

        # Apply global search
        if search_value:
            base_data = [item for item in base_data if any(str(value).lower().find(search_value.lower()) != -1 for value in item.values())]

        # Calculate the total number of records after filtering
        records_filtered = len(base_data)

        # Apply pagination
        if length < 0:
            length = len(base_data)
        base_data = base_data[start:start + length]

        # Calculate row_count based on current page and length
        page_number = start // length + 1
        row_count_start = (page_number - 1) * length + 1


        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'regdate': item.get('regdate').strftime('%d-%b-%Y %H:%M:%S') if item.get('regdate') else 'n/a',
                'lastedit': item.get('lastedit').strftime('%d-%b-%Y %H:%M:%S') if item.get('lastedit') else 'n/a',
                'names': item.get('names'),
                'qty': item.get('qty'),
                'price': '{:,.2f}'.format(item.get('price'))+" TZS",
                'expiry': item.get('expiry').strftime('%d-%b-%Y') if item.get('expiry') else 'n/a',
                'exp_status': item.get('exp_status'),
                'info': item.get('info'),
                'action': '',
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
        }
        return JsonResponse(ajax_response)
    return render(request, 'shop/inventory.html')

# inventory actions
@never_cache
@login_required
@admin_required()
def product_actions(request):
    if request.method == 'POST':
        try:
            edit_product = request.POST.get('edit_product')
            delete_product = request.POST.get('delete_product')
            product_qty = request.POST.get('product_qty')

            if delete_product:
                product_instance = Product.objects.get(id=delete_product)
                product_instance.deleted = True
                product_instance.save()

                Cart.objects.filter(product=product_instance).delete()
                return JsonResponse({'success': True, 'url': reverse('inventory_page')})
            
            elif edit_product:
                product_instance = Product.objects.get(id=edit_product)
                form = ProductForm(request.POST, instance=product_instance)

                if form.is_valid():
                    prod = form.save(commit=False)
                    prod.editedBy = request.user
                    prod.qty = product_instance.qty
                    prod.lastEdited = datetime.now().replace(tzinfo=pytz.UTC)
                    prod.comment = form.cleaned_data.get('comment') or None
                    prod.save()

                    return JsonResponse({'success': True, 'update_success': True, 'sms': 'Product details updated successfully!'})
                else:
                    errorMsg = form.errors.get('names', ["Failed to update information"])[0]
                    return JsonResponse({'success': False, 'sms': errorMsg})
            
            elif product_qty:
                product = Product.objects.get(id=product_qty)
                product.qty += float(request.POST.get('new_qty'))
                product.save()

                return JsonResponse({'success': True, 'qty': format_num(product.qty), 'sms': 'Product quantity updated!'})
            
            else:
                form = ProductForm(request.POST)
                if form.is_valid():
                    prod = form.save(commit=False)
                    prod.addedBy = request.user
                    prod.save()

                    return JsonResponse({'success': True, 'sms': 'New product added successfully!'})
                else:
                    errorMsg = form.errors.get('names', ["Failed to add new product."])[0]
                    return JsonResponse({'success': False, 'sms': errorMsg})

        except Exception as e:
            return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})
        
    return JsonResponse({'success': False, 'sms': 'Invalid data'})

# product details
@never_cache
@login_required
@admin_required()
def product_details(request, product_id):
    product_instance = Product.objects.filter(id=product_id, deleted=False).first()
    if request.method == 'GET' and product_instance:
        product_info = {
            'id': product_instance.id,
            'regdate': product_instance.regdate.strftime('%d-%b-%Y %H:%M:%S'),
            'regby': f'{product_instance.addedBy.fullname} ({product_instance.addedBy.username})',
            'last_edit': product_instance.lastEdited.strftime('%d-%b-%Y %H:%M:%S') if product_instance.lastEdited else 'n/a',
            'editor': f'{product_instance.editedBy.fullname} ({product_instance.editedBy.username})' if product_instance.editedBy else 'n/a',
            'names': product_instance.names,
            'qty': format_num(product_instance.qty),
            'stock': product_instance.qty,
            'price': format_num(product_instance.price),
            'expiry_date': product_instance.expiry or '',
            'expiry': product_instance.expiry.strftime('%d-%b-%Y') if product_instance.expiry else 'n/a',
            'exp_status': int(product_instance.expiry is not None and product_instance.expiry <= date.today()),
            'comment': product_instance.comment or '',
        }
        return render(request, 'shop/inventory.html', {'product': product_info})
    return redirect('inventory_page')

# Sales page
@never_cache
@login_required
def sales_page(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        queryset = Product.objects.exclude(deleted=True)

        # Base data from queryset
        base_data = []
        for product in queryset:
            if product.expiry is None or (product.expiry is not None and product.expiry >= date.today()):
                cart_count = 0
                if Cart.objects.filter(user=request.user, product=product).exists():
                    cart_item = Cart.objects.filter(user=request.user, product=product).first()
                    cart_count = cart_item.qty
                product_object = {
                    'id': product.id,
                    'names': product.names,
                    'qty': product.qty,
                    'price': product.price,
                    'cart': cart_count
                }
                base_data.append(product_object)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'names',
            2: 'qty',
            3: 'price',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'names')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    base_data = [item for item in base_data if filter_items(column_field, column_search, item, ('qty', 'price'))]

        # Apply global search
        if search_value:
            base_data = [item for item in base_data if any(str(value).lower().find(search_value.lower()) != -1 for value in item.values())]

        # Calculate the total number of records after filtering
        records_filtered = len(base_data)

        # Apply pagination
        if length < 0:
            length = len(base_data)
        base_data = base_data[start:start + length]

        # Calculate row_count based on current page and length
        page_number = start // length + 1
        row_count_start = (page_number - 1) * length + 1


        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'names': item.get('names'),
                'qty': format_num(item.get('qty')),
                'price': '{:,.2f}'.format(item.get('price'))+" TZS",
                'sell_qty': format_num(item.get('qty')),
                'cart': format_num(item.get('cart')),
                'action': '',
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
        }
        return JsonResponse(ajax_response)
    
    cart = Cart.objects.filter(user=request.user).order_by('id')
    grand_total, cart_items = sum(item.product.price * item.qty for item in cart), []

    for item in cart:
        cart_items.append({
            'id': item.id,
            'name': item.product.names,
            'price': f"TZS. {item.product.price:,.2f}",
            'qty': format_num(item.qty),
            'max_qty': item.product.qty
        })

    context = {
        'cart_label': str(cart.count()) if cart.count() < 10 else '9+',
        'cart_count': cart.count(),
        'cart_items': cart_items,
        'total': f"TZS. {grand_total:,.2f}"
    }
    return render(request, 'shop/sales.html', context)

# Sales actions
def sales_actions(request):
    if request.method == 'POST':
        try:
            add_to_cart = request.POST.get('cart_add')
            cart_delete = request.POST.get('cart_delete')
            clear_cart = request.POST.get('clear_cart')
            checkout = request.POST.get('checkout')

            if add_to_cart:
                product_id = request.POST.get('product')
                product_qty = float(request.POST.get('qty'))
                product = Product.objects.get(id=product_id)

                if product_qty > product.qty:
                    return JsonResponse({'success': False, 'sms': f'Qty exceeded available stock ({product.qty}).'})
                
                cart_item, created = Cart.objects.update_or_create(
                    product=product,
                    user=request.user,
                    defaults={'qty': product_qty}
                )

                cart_count = Cart.objects.filter(user=request.user).count()
                cart_count = cart_count if cart_count < 10 else '9+'

                return JsonResponse({'success': True, 'sms': f'{format_num(product_qty)} items added to cart.', 'cart': cart_count})
            
            elif cart_delete:
                cart_item = Cart.objects.get(id=cart_delete)
                cart_item.delete()

                items_remaining = Cart.objects.filter(user=request.user)
                cart_count = items_remaining.count() if items_remaining.count() < 10 else '9+'
                
                grand_total = sum(item.product.price * item.qty for item in items_remaining)

                return JsonResponse({'success': True, 'cart': cart_count, 'grand_total': "TZS. " + '{:,.2f}'.format(grand_total)})

            elif clear_cart:
                Cart.objects.filter(user=request.user).delete()
                return JsonResponse({'success': True})
            
            elif checkout:
                full_cart = Cart.objects.filter(user=request.user)
                grand_amount, qty_status, qty_products = 0.0, True, []

                for item in full_cart:
                    grand_amount += item.product.price * item.qty
                    if item.qty > item.product.qty:
                        qty_status = False
                        qty_products.append(item.product.names)

                if qty_status:
                    sale_transaction = Sales.objects.create(
                        user=request.user,
                        amount=grand_amount
                    )

                    for item in full_cart:
                        Sale_items.objects.create(
                            sale=sale_transaction,
                            product=item.product,
                            price=item.product.price,
                            qty=item.qty
                        )
                        item.product.qty -= item.qty
                        item.product.save()
                        item.delete()
                    
                    return JsonResponse({'success': True, 'sms': 'Checkout completed successfully!'})
                else:
                    products_str = ', '.join(qty_products)
                    return JsonResponse({'success': False, 'sms': f'Quantity mismatch for: <b>{products_str}</b>.<br>Reload page and correct qty.'})
        
        except Exception as e:
            print(e)
            return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})
    
    return JsonResponse({'success': False, 'sms': 'Invalid data'})

# Sales report page
@never_cache
@login_required
def sales_report(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        queryset = Sales.objects.filter(user=request.user)
        if request.user.is_admin:
            queryset = Sales.objects.all()

        # Date range filtering
        sale_start = parse_datetime(request.POST.get('start_date'), format_datetime, to_utc=True)
        sale_end = parse_datetime(request.POST.get('end_date'), format_datetime, to_utc=True)
        date_range_filters = Q()

        if sale_start and sale_end:
            date_range_filters |= Q(saledate__range=(sale_start, sale_end))
        else:
            if sale_start:
                date_range_filters |= Q(saledate__gte=sale_start)
            elif sale_end:
                date_range_filters |= Q(saledate__lte=sale_end)

        if date_range_filters:
            queryset = queryset.filter(date_range_filters)

        # Base data from queryset
        base_data, grand_total = [], 0.0
        for sale in queryset:
            grand_total += sale.amount
            sale_items = Sale_items.objects.filter(sale=sale)
            sales_data = [
                {
                    'count': idx + 1,
                    'names': item.product.names,
                    'price': '{:,.2f} TZS'.format(item.price),
                    'qty': item.qty,
                    'total': '{:,.2f} TZS'.format(item.price * item.qty)
                }
                for idx, item in enumerate(sale_items)
            ]
            
            sale_object = {
                'id': sale.id,
                'saledate': sale.saledate,
                'user': sale.user.username,
                'amount': sale.amount,
                'sale_items': sales_data,
                'user_info': reverse('user_profile') if sale.user.is_admin else reverse('user_details', kwargs={'user_id': sale.user_id})
            }
            
            base_data.append(sale_object)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'sale_items',
            1: 'id',
            2: 'saledate',
            3: 'user',
            4: 'amount',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'saledate')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    base_data = [item for item in base_data if filter_items(column_field, column_search, item, ('amount'))]

        # Apply global search
        if search_value:
            base_data = [item for item in base_data if any(str(value).lower().find(search_value.lower()) != -1 for value in item.values())]

        # Calculate the total number of records after filtering
        records_filtered = len(base_data)

        # Apply pagination
        if length < 0:
            length = len(base_data)
        base_data = base_data[start:start + length]

        # Calculate row_count based on current page and length
        page_number = start // length + 1
        row_count_start = (page_number - 1) * length + 1


        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'saledate': item.get('saledate').strftime('%d-%b-%Y %H:%M:%S'),
                'user': item.get('user'),
                'amount': '{:,.2f}'.format(item.get('amount'))+" TZS",
                'items': item.get('sale_items'),
                'user_info': item.get('user_info'),
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
            'grand_total': grand_total,
        }
        return JsonResponse(ajax_response)
    return render(request, 'shop/report.html')

# Sale items report
@never_cache
@login_required
def sales_items_report(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        queryset = Sale_items.objects.filter(sale__user=request.user)
        if request.user.is_admin:
            queryset = Sale_items.objects.all()

        # Date range filtering
        sale_start = parse_datetime(request.POST.get('start_date'), format_datetime, to_utc=True)
        sale_end = parse_datetime(request.POST.get('end_date'), format_datetime, to_utc=True)
        date_range_filters = Q()

        if sale_start and sale_end:
            date_range_filters |= Q(sale__saledate__range=(sale_start, sale_end))
        else:
            if sale_start:
                date_range_filters |= Q(sale__saledate__gte=sale_start)
            elif sale_end:
                date_range_filters |= Q(sale__saledate__lte=sale_end)

        if date_range_filters:
            queryset = queryset.filter(date_range_filters)

        # Base data from queryset
        base_data, sales_total = [], 0.0
        for item in queryset:
            sales_total += item.price * item.qty
            sale_object = {
                'id': item.id,
                'saledate': item.sale.saledate,
                'product': item.product.names,
                'price': item.price,
                'qty': item.qty,
                'amount': item.price * item.qty,
                'user': item.sale.user.username,
                'user_info': reverse('user_profile') if item.sale.user.is_admin else reverse('user_details', kwargs={'user_id': item.sale.user_id})
            }
            
            base_data.append(sale_object)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'saledate',
            2: 'product',
            3: 'price',
            4: 'qty',
            5: 'amount',
            6: 'user'
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'saledate')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    base_data = [item for item in base_data if filter_items(column_field, column_search, item, ('price', 'qty', 'amount'))]

        # Apply global search
        if search_value:
            base_data = [item for item in base_data if any(str(value).lower().find(search_value.lower()) != -1 for value in item.values())]

        # Calculate the total number of records after filtering
        records_filtered = len(base_data)

        # Apply pagination
        if length < 0:
            length = len(base_data)
        base_data = base_data[start:start + length]

        # Calculate row_count based on current page and length
        page_number = start // length + 1
        row_count_start = (page_number - 1) * length + 1


        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'saledate': item.get('saledate').strftime('%d-%b-%Y %H:%M:%S'),
                'product': item.get('product'),
                'price': '{:,.2f}'.format(item.get('price'))+" TZS",
                'qty': '{:,.0f}'.format(item.get('qty')),
                'amount': '{:,.2f}'.format(item.get('amount'))+" TZS",
                'user': item.get('user'),
                'user_info': item.get('user_info'),
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
            'grand_total': sales_total,
        }
        return JsonResponse(ajax_response)
    return render(request, 'shop/items_report.html')