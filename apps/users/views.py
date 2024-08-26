from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import CustomUserForm, CustomAuthenticationForm
from .models import CustomUser
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from utils.util_functions import parse_datetime


# datetime format
format_datetime = "%Y-%m-%d %H:%M:%S.%f"


@never_cache
def authenticate_user(request):
    response = JsonResponse({'success': False, 'sms': 'Invalid request'})
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None and not user.blocked and not user.deleted:
                login(request, user)
                response = JsonResponse({'success': True, 'url': reverse('dashboard_page')})
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
def users_requests(request):
    if request.method == 'POST':
        try:
            edit_user = request.POST.get('edit_user')
            delete_user = request.POST.get('delete_user')
            block_user = request.POST.get('block_user')
            reset_password = request.POST.get('reset_password')
            if delete_user:
                user_instance = CustomUser.objects.get(id=delete_user)
                user_instance.deleted = True
                user_instance.save()
                fdback = {'success': True, 'url':reverse('users_list')}
            elif block_user:
                user_instance = CustomUser.objects.get(id=block_user)
                user_instance.blocked = not user_instance.blocked
                user_instance.save()
                fdback = {'success': True}
            elif edit_user:
                user_instance = CustomUser.objects.get(id=edit_user)
                fullname = request.POST.get('fullname').strip()
                fullname = ' '.join(word.capitalize() for word in fullname.split())
                username = request.POST.get('username').strip().capitalize()
                phone = request.POST.get('phone').strip()
                if len(phone) == 0:
                    phone = None
                comment = request.POST.get('comment').strip()
                if len(comment) == 0:
                    comment = None

                if len(username) < 5:
                    return JsonResponse({'success': False, 'sms': 'Username should be atleast 5 alphabets long.'})
                
                if not username.isalpha():
                    return JsonResponse({'success': False, 'sms': 'Username should contain only alphabets A-Z.'})
                
                if CustomUser.objects.filter(username=username, deleted=False).exclude(id=edit_user).exists():
                    return JsonResponse({'success': False, 'sms': 'This username is already used by another user.'})
                
                if phone is not None and not phone.isdigit():
                    return JsonResponse({'status': False, 'sms': 'Please use a 10-digit phone number.'})
                
                if phone is not None and len(phone) != 10:
                    return JsonResponse({'status': False, 'sms': 'Please use a 10-digit phone number.'})
                
                if phone is not None and CustomUser.objects.filter(phone=phone, deleted=False).exclude(id=edit_user).exists():
                    return JsonResponse({'success': False, 'sms': 'This phone is already used by another user.'})
                
                user_instance.fullname = fullname
                user_instance.username = username
                user_instance.phone = phone
                user_instance.comment = comment
                user_instance.save()
                fdback = {'success': True, 'update_success':True, 'sms': 'User information updated.'}
            elif reset_password:
                user_instance = CustomUser.objects.get(id=reset_password)
                new_password = user_instance.username.upper()
                user_instance.set_password(new_password)
                user_instance.save()
                fdback = {'success': True}
            else:
                form = CustomUserForm(request.POST)
                if form.is_valid():
                    form.save()
                    fdback = {'success': True, 'sms': 'Registration completed!'}
                else:
                    errorMsg = ""
                    if 'username' in form.errors:
                        errorMsg = form.errors['username'][0]
                    if 'phone' in form.errors:
                        errorMsg = form.errors['phone'][0]
                    fdback = {'success': False, 'sms': errorMsg}
        except Exception as e:
            fdback = {'success': False, 'sms': 'Unknown error occured'}
        return JsonResponse(fdback)
    return JsonResponse({'success': False, 'sms': 'Invalid data'})

@never_cache
@login_required
def user_details(request, user_id):
    if request.method == 'GET' and CustomUser.objects.filter(id=user_id, deleted=False).exists():
        user_instance = CustomUser.objects.get(id=user_id)
        user_data = {
            'id': user_instance.id,
            'regdate': user_instance.regdate.strftime('%d-%b-%Y %H:%M:%S'),
            'fullname': user_instance.fullname,
            'username': user_instance.username,
            'phone': user_instance.phone if user_instance.phone else '',
            'status': "Blocked" if user_instance.blocked else "Active",
            'comment': user_instance.comment if user_instance.comment else '',
        }
        context = {
            'user_info': user_id,
            'user': user_data,
        }
        return render(request, 'users/users.html', context)
    return redirect('users_page')