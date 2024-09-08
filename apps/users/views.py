from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import CustomUserForm, CustomAuthenticationForm
from .models import CustomUser
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from utils.util_functions import parse_datetime, admin_required


# datetime format
format_datetime = "%Y-%m-%d %H:%M:%S.%f"

def handle_user_deletion(user_id):
    user_instance = CustomUser.objects.get(id=user_id)
    user_instance.deleted = True
    user_instance.save()
    return {'success': True, 'url': reverse('users_list')}

def handle_user_blocking(user_id):
    user_instance = CustomUser.objects.get(id=user_id)
    user_instance.blocked = not user_instance.blocked
    user_instance.save()
    return {'success': True}

def validate_user_data(username, phone, edit_user=None):
    if len(username) < 5:
        return {'success': False, 'sms': 'Username should be at least 5 alphabets long.'}
    if not username.isalpha():
        return {'success': False, 'sms': 'Username should contain only alphabets A-Z.'}
    if CustomUser.objects.filter(username=username, deleted=False).exclude(id=edit_user).exists():
        return {'success': False, 'sms': 'This username is already used by another user.'}
    if phone is not None:
        if not phone.isdigit() or len(phone) != 10:
            return {'status': False, 'sms': 'Please use a valid 10-digit phone number.'}
        if CustomUser.objects.filter(phone=phone, deleted=False).exclude(id=edit_user).exists():
            return {'success': False, 'sms': 'This phone is already used by another user.'}
    return None

def handle_user_editing(user_instance, fullname, username, phone, comment):
    validation_errors = validate_user_data(username, phone, user_instance.id)
    if validation_errors:
        return validation_errors

    user_instance.fullname = fullname
    user_instance.username = username
    user_instance.phone = phone
    user_instance.comment = comment
    user_instance.save()
    return {'success': True, 'update_success': True, 'sms': 'User information updated.'}

def handle_password_reset(user_id):
    user_instance = CustomUser.objects.get(id=user_id)
    new_password = user_instance.username.upper()
    user_instance.set_password(new_password)
    user_instance.save()
    return {'success': True}

def handle_user_registration(post_data):
    form = CustomUserForm(post_data)
    if form.is_valid():
        form.save()
        return {'success': True, 'sms': 'Registration completed!'}
    errorMsg = form.errors.get('username', form.errors.get('phone', ['Unknown error, reload & try again'])[0])[0]
    return {'success': False, 'sms': errorMsg}


@never_cache
def authenticate_user(request):
    response = JsonResponse({'success': False, 'sms': 'Invalid request'})
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            next_url = request.POST.get('next_url', reverse('dashboard_page'))
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None and not user.blocked and not user.deleted:
                login(request, user)
                response = JsonResponse({'success': True, 'url': next_url})
                response.set_cookie('user_id', user.username)
        else:
            response = JsonResponse({'success': False, 'sms': form.errors['__all__'][0], 'error':form.errors})
    return response


@login_required
def user_signout(request):
  if request.user.is_authenticated:
    logout(request)
  return redirect(reverse('index_page'))

@never_cache
@login_required
@admin_required()
def manage_users(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        # Base queryset
        queryset = CustomUser.objects.filter(deleted=False).exclude(id=request.user.id)

        # Date range filtering
        start_date = parse_datetime(request.POST.get('startdate'), format_datetime, to_utc=True)
        end_date = parse_datetime(request.POST.get('enddate'), format_datetime, to_utc=True)
        date_range_filters = Q()

        if start_date and end_date:
            date_range_filters |= Q(regdate__range=(start_date, end_date))
        else:
            if start_date:
                date_range_filters |= Q(regdate__gte=start_date)
            elif end_date:
                date_range_filters |= Q(regdate__lte=end_date)

        if date_range_filters:
            queryset = queryset.filter(date_range_filters)


        # Base data from queryset
        base_data = []
        for user in queryset:
            user_data = {
                'id': user.id,
                'regdate': user.regdate,
                'fullname': user.fullname,
                'username': user.username,
                'phone': user.phone if user.phone else "N/A",
                'status': "Blocked" if user.blocked else "Active",
                'info': reverse('user_details', kwargs={'user_id': int(user.id)})
            }
            base_data.append(user_data)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'regdate',
            2: 'fullname',
            3: 'username',
            4: 'phone',
            5: 'status',
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
                        if column_field == 'status':
                            if column_search.lower() == column_value:
                                filtered_base_data.append(item)
                        else:
                            if column_search.lower() in column_value:
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


        # Final data to be returned to ajax call
        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'regdate': item.get('regdate').strftime('%d-%b-%Y'),
                'fullname': item.get('fullname'),
                'username': item.get('username'),
                'phone': item.get('phone'),
                'status': item.get('status'),
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
    return render(request, 'users/users.html')


@never_cache
@login_required
@admin_required()
def users_requests(request):
    if request.method == 'POST':
        try:
            edit_user = request.POST.get('edit_user')
            delete_user = request.POST.get('delete_user')
            block_user = request.POST.get('block_user')
            reset_password = request.POST.get('reset_password')

            if delete_user:
                fdback = handle_user_deletion(delete_user)
            elif block_user:
                fdback = handle_user_blocking(block_user)
            elif edit_user:
                user_instance = CustomUser.objects.get(id=edit_user)
                fullname = ' '.join(word.capitalize() for word in request.POST.get('fullname', '').strip().split())
                username = request.POST.get('username', '').strip().capitalize()
                phone = request.POST.get('phone', '').strip() or None
                comment = request.POST.get('comment', '').strip() or None
                fdback = handle_user_editing(user_instance, fullname, username, phone, comment)
            elif reset_password:
                fdback = handle_password_reset(reset_password)
            else:
                fdback = handle_user_registration(request.POST)
        except Exception as e:
            fdback = {'success': False, 'sms': 'Unknown error, reload & try again'}
        return JsonResponse(fdback)
    return JsonResponse({'success': False, 'sms': 'Invalid data'})


@never_cache
@login_required
@admin_required()
def user_details(request, user_id):
    if request.method == 'GET' and not user_id == request.user.id:
        try:
            user_instance = CustomUser.objects.get(id=user_id, deleted=False)
        except CustomUser.DoesNotExist:
            return redirect('users_page')

        user_data = {
            'id': user_instance.id,
            'regdate': user_instance.regdate.strftime('%d-%b-%Y %H:%M:%S'),
            'fullname': user_instance.fullname,
            'username': user_instance.username,
            'phone': user_instance.phone or '',
            'status': "Blocked" if user_instance.blocked else "Active",
            'comment': user_instance.comment or '',
        }
        return render(request, 'users/users.html', {'user_info': user_id, 'user': user_data})
    return redirect('users_page')


@never_cache
@login_required
def user_profile_page(request):
    if request.method == 'POST':
        try:
            user = request.user
            change_contact = request.POST.get('change_contact')
            update_profile = request.POST.get('update_profile')
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password1')
            confirm_password = request.POST.get('new_password2')

            if change_contact:
                if not change_contact.isdigit() or len(change_contact) != 10:
                    return JsonResponse({'success': False, 'sms': 'Please use a valid 10-digit phone number.'})
                if CustomUser.objects.filter(phone=change_contact, deleted=False).exclude(id=user.id).exists():
                    return JsonResponse({'success': False, 'sms': 'This phone number is already used by another account.'})
                
                user.phone = change_contact
                user.save()
                return JsonResponse({'success': True, 'sms': 'Contact updated successfully'})

            elif update_profile:
                fullname = ' '.join(word.capitalize() for word in request.POST.get('fullname').strip().split())
                username = request.POST.get('username').strip().capitalize()
                phone = request.POST.get('phone').strip() or None

                if len(username) < 5:
                    return JsonResponse({'success': False, 'sms': 'Username should be at least 5 alphabets long.'})
                if not username.isalpha():
                    return JsonResponse({'success': False, 'sms': 'Username should contain only alphabets A-Z.'})
                if CustomUser.objects.filter(username=username, deleted=False).exclude(id=user.id).exists():
                    return JsonResponse({'success': False, 'sms': 'This username is already used by another user.'})
                if phone and (not phone.isdigit() or len(phone) != 10):
                    return JsonResponse({'success': False, 'sms': 'Please use a valid 10-digit phone number.'})
                if phone and CustomUser.objects.filter(phone=phone, deleted=False).exclude(id=user.id).exists():
                    return JsonResponse({'success': False, 'sms': 'This phone number is already used by another account.'})
                
                user.fullname = fullname
                user.username = username
                user.phone = phone
                user.save()
                return JsonResponse({'success': True, 'update_success': True, 'sms': 'Profile updated successfully.'})

            else:
                if not authenticate(username=user.username, password=old_password):
                    return JsonResponse({'success': False, 'sms': 'Incorrect current password!'})
                if len(new_password) < 8:
                    return JsonResponse({'success': False, 'sms': f'Password should be 8 or more characters long, (not {len(new_password)})'})
                if new_password != confirm_password:
                    return JsonResponse({'success': False, 'sms': "Passwords should match in both fields"})

                user.set_password(new_password)
                user.save()
                login(request, user, backend='shop_app.password_backend.CaseInsensitiveModelBackend')
                return JsonResponse({'success': True, 'sms': 'Password changed successfully'})

        except Exception as e:
            print(e)
            return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})

    data = {
        'regdate': request.user.regdate.strftime('%d-%b-%Y %H:%M:%S'),
        'fullname': request.user.fullname,
        'username': request.user.username,
        'phone': request.user.phone or "",
        'mobile': request.user.phone or "N/A",
    }
    return render(request, 'users/profile.html', {'profile': data})
