from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q, Case, When, Value, DateField, DateTimeField, F
from datetime import datetime, date
from .models import Product
from .forms import ProductForm
from utils.util_functions import parse_datetime
import os
import json
import pytz


# datetime format
format_datetime = "%Y-%m-%d %H:%M:%S.%f"

# dashboard page
@never_cache
@login_required
def dashboard_page(request):
    return render(request, 'shop/dashboard.html')

# inventory page
@never_cache
@login_required
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
            date_range_filters |= Q(expiry_date__range=(exp_start, exp_end))
        else:
            if exp_start:
                date_range_filters |= Q(expiry_date__gte=exp_start)
            elif exp_end:
                date_range_filters |= Q(expiry_date__lte=exp_end)

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
                    filtered_base_data = []
                    for item in base_data:
                        column_value = str(item.get(column_field, '')).lower()
                        if column_field in ('qty', 'price'):
                            if column_search.startswith('-') and column_search[1:].isdigit():
                                max_value = int(column_search[1:])
                                item_value = float(column_value) if column_value else 0.0
                                if item_value <= max_value:
                                    filtered_base_data.append(item)
                            elif column_search.endswith('-') and column_search[:-1].isdigit():
                                min_value = int(column_search[:-1])
                                item_value = float(column_value) if column_value else 0.0
                                if item_value >= min_value:
                                    filtered_base_data.append(item)
                            elif column_search.isdigit():
                                target_value = float(column_search.replace(',', ''))
                                item_value = float(column_value) if column_value else 0.0
                                if item_value == target_value:
                                    filtered_base_data.append(item)
                        elif column_search.lower() in column_value:
                            filtered_base_data.append(item)

                    base_data = filtered_base_data

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
def product_actions(request):
    if request.method == 'POST':
        try:
            edit_product = request.POST.get('edit_product')
            delete_product = request.POST.get('delete_product')
            if delete_product:
                product_instance = Product.objects.get(id=delete_product)
                product_instance.deleted = True
                product_instance.save()
                fdback = {'success': True, 'url':reverse('inventory_page')}
            elif edit_product:
                product_instance = Product.objects.get(id=edit_product)
                form = ProductForm(request.POST, instance=product_instance)
                if form.is_valid():
                    prod = form.save(commit=False)
                    prod.editedBy = request.user
                    prod.lastEdited = datetime.now().replace(tzinfo=pytz.UTC)
                    prod.comment = form.cleaned_data.get('comment') or None
                    prod.save()
                    fdback = {'success': True, 'sms': 'Product details updated successfully!'}
                else:
                    errorMsg = "Failed to update information"
                    if 'names' in form.errors:
                        errorMsg = form.errors['names'][0]
                    fdback = {'success': False, 'sms': errorMsg}
            else:
                form = ProductForm(request.POST)
                if form.is_valid():
                    prod = form.save(commit=False)
                    prod.addedBy = request.user
                    prod.save()
                    fdback = {'success': True, 'sms': 'New product added successfully!'}
                else:
                    errorMsg = "Failed to add new product."
                    if 'names' in form.errors:
                        errorMsg = form.errors['names'][0]
                    fdback = {'success': False, 'sms': errorMsg}
        except Exception as e:
            fdback = {'success': False, 'sms': 'Unknown error occured'}
        return JsonResponse(fdback)
    return JsonResponse({'success': False, 'sms': 'Invalid data'})




# product details
@never_cache
@login_required
def product_details(request, product_id):
    if request.method == 'GET' and Product.objects.filter(id=product_id, deleted=False).exists():
        product_instance = Product.objects.get(id=product_id)
        product_info = {
            'id': product_instance.id,
            'regdate': product_instance.regdate.strftime('%d-%b-%Y %H:%M:%S'),
            'regby': f'{product_instance.addedBy.fullname} ({product_instance.addedBy.username})',
            'last_edit': product_instance.lastEdited.strftime('%d-%b-%Y %H:%M:%S') if product_instance.lastEdited else '-',
            'editor': f'{product_instance.editedBy.fullname} ({product_instance.editedBy.username})' if product_instance.editedBy else '-',
            'names': product_instance.names,
            'qty': product_instance.qty,
            'price': product_instance.price,
            'expiry_date': product_instance.expiry if product_instance.expiry else '',
            'expiry': product_instance.expiry.strftime('%d-%b-%Y') if product_instance.expiry else '-',
            'comment': product_instance.comment if product_instance.comment else '',
        }
        context = {
            'product_info': product_id,
            'product': product_info,
        }
        return render(request, 'shop/inventory.html', context)
    return redirect('inventory_page')