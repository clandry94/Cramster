from django.shortcuts import get_object_or_404, render, render_to_response
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.context_processors import csrf
from django.db.models import Q
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .routes.serializers import *
from .routes.viewsets import *
from .models import *
from .forms import *
# Create your views here.

def index(request):
	args={}
	if request.user.is_active:
		open_order = Order.objects.filter(user=request.user.storeuser, paid=False)
		if open_order != False:
			args['open_order'] = True
	args['oversell'] = Product.objects.filter(stock_quantity__lte=10)
	return render(request, 'store/base.html', args)


def search(request, filter=None):
	if 'q' in request.GET and request.GET['q']:
		q = request.GET['q']
		if 'BN' in request.GET:
			products = Product.objects.order_by('product_name').filter(Q(product_name__icontains=q) | Q(description__icontains=q))
		elif 'MP' in request.GET:
			products = Product.objects.order_by('-price').filter(Q(product_name__icontains=q) | Q(description__icontains=q))
		elif 'LP' in request.GET:
			products = Product.objects.order_by('price').filter(Q(product_name__icontains=q) | Q(description__icontains=q))
		else:
			products = Product.objects.filter(Q(product_name__icontains=q) | Q(description__icontains=q))
		result = {
			'products': products,
			'query': q,
		}
		return render(request, 'store/search_results.html', result)

	else:
		return render(request, 'store/base.html', {'empty_search': True})

def oversell(request):

	oversell = Product.objects.filter(stock_quantity__lte=10)

	return render(request, 'store/oversell.html', {'oversell': oversell})

# Login Views
def login(request):
	c = {}
	c.update(csrf(request))
	return render(request, 'store/login.html', c)

def auth_view(request):
	username = request.POST.get('username', '')
	password = request.POST.get('password', '')
	user = auth.authenticate(username=username, password=password)

	if user is not None:
		auth.login(request, user)
		return HttpResponseRedirect('/')
	else:
		return HttpResponseRedirect('/accounts/invalid/')

def invalid_login(request):
	c = {}
	c.update(csrf(request))
	return render(request, 'store/login.html', {'invalid': True})

def logout(request):
	auth.logout(request)
	return HttpResponseRedirect('/')

def register_user(request):
	if request.method == 'POST':
		form = UserForm(request.POST)
		store_form = StoreUserForm(request.POST)
		username = request.POST.get('username', '')

		if form.is_valid() * store_form .is_valid():
			form.save()

			u = User.objects.get(username=username)

			temp = StoreUser(auth_user=u)

			user = StoreUserForm(request.POST, instance=temp)

			user.save()
			return render(request, 'store/login.html')

	args = {}
	args.update(csrf(request))

	args['form'] = UserForm()
	args['user_info'] = StoreUserForm()

	return render(request, 'store/register.html', args)

def settings(request):
	current_user = User.objects.get(username=request.user.username)
	error = False

	if request.method == 'POST':

		form1 = UserForm(request.POST, instance=current_user)
		form2 = StoreUserForm(request.POST, instance=current_user.storeuser)

		if form1.is_valid() * form2.is_valid():
			form1.save()
			form2.save()
			return HttpResponseRedirect('/accounts/login/')

		error = True


	args = {}
	args.update(csrf(request))

	if error:
		args['error'] = True
	args['form1'] = UserForm(instance=current_user)
	args['form2'] = StoreUserForm(instance=current_user.storeuser)
	args['current_user'] = current_user
	return render(request, 'store/settings.html', args)

def delete_user(request, user_id):
	try:
		user_id = int(user_id)
	except ValueError:
		raise Http404()

	if user_id == request.user.id:
		auth.logout(request)

	user_to_delete = User.objects.get(pk=user_id)
	user_to_delete.delete()

	return render(request, 'store/base.html')

def product_catalog(request, filter=None):
	if filter == '1':
		products = Product.objects.order_by('product_name')
	elif filter == '2':
		products = Product.objects.order_by('-price')
	elif filter == '3':
		products = Product.objects.order_by('price')
	else:
		products = Product.objects.all()
	return render(request, 'store/product_catalog.html', { "products": products })

def add_product(request):
	if request.method == 'POST':

		form = NewProductForm(request.POST)

		if form.is_valid():
			form.save()
			return HttpResponseRedirect('/products/')

	args = {}
	args.update(csrf(request))

	args['form'] = NewProductForm()
	return render(request, 'store/product_add.html', args)

def edit_product(request, product_id="1"):
	try:
		product_id = int(product_id)
	except ValueError:
		raise Http404()

	if request.method == 'POST':

		current_product = Product.objects.get(pk=product_id)
		form = ProductForm(request.POST, instance=current_product)

		if form.is_valid():
			form.save()
			return HttpResponseRedirect('/products/')

	product = get_object_or_404(Product, pk=product_id)

	args = {}
	args.update(csrf(request))

	args['form'] = ProductForm(instance=product)
	args['product'] = product
	return render(request, 'store/product_edit.html', args)

def delete_product(request, product_id):
	try:
		product_id = int(product_id)
	except ValueError:
		raise Http404()

	if request.method == 'POST':
		product = get_object_or_404(Product, pk=product_id)
		product.delete()
		return HttpResponseRedirect('/products/')

def orders(request):
	args = {}
	args.update(csrf(request))
	args['error'] = ""
	args['ProductOrderForm'] = ProductOrderForm()

	if request.method == 'POST':

		order = Order(user=request.user.storeuser, paid=False)
		order.save()
		product_order = ProductOrder(order=order)
		form = ProductOrderForm(request.POST, instance=product_order)

		if form.is_valid():
			form.save()
			args['order_id'] = order.pk
			return render(request, 'store/orders_more.html', args)
		else:
			order.delete()
			args['error'] = "Order Submission Failed!"
			render(request, 'store/order_form.html', args)

	return render(request, 'store/order_form.html', args)

def orders_more(request, order_id="1"):
	try:
		order_id = int(order_id)
	except ValueError:
		raise Http404()

	args = {}
	args.update(csrf(request))

	args['form'] = ProductOrderForm()
	args['order_id'] = order_id

	current_order = Order.objects.get(pk=order_id)

	if request.method == 'POST':

		product_order = ProductOrder(order=current_order)
		form = ProductOrderForm(request.POST, instance=product_order)
		if form.is_valid():
			form.save()
			return render(request, 'store/orders_more.html', args)

	return render(request, 'store/orders_more.html', args)


def orders_checkout(request, order_id="1"):
	try:
		order_id = int(order_id)
	except ValueError:
		raise Http404()
	args={}

	current_order = Order.objects.get(pk=order_id)
	product_orders = ProductOrder.objects.filter(order=current_order)

	args['current_order'] = current_order
	args['order_id'] = order_id
	price = 0
	for product_order in product_orders:
		price = price + ( product_order.quantity * product_order.product.price )

	args['price'] = price

	if request.method == 'POST':
		payment = request.POST.get('payment', '')

		if price == int(payment):
			current_order.paid = True
			current_order.save()
			args['pay_success'] = True
			return render(request, 'store/orders_checkout.html', args)
		else:
			args['pay_fail'] = True
			return render(request, 'store/orders_checkout.html', args)

	return render(request, 'store/orders_checkout.html', args)


def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'store/supplier_list.html', { "suppliers": suppliers })

def user_list(request):
	users = User.objects.all()
	return render(request, 'store/user_list.html', { "users": users })

def order_list(request):
	orders = Order.objects.all()
	return render(request, 'store/order_list.html', { "orders": orders })

def open_orders(request):
	open_orders = Order.objects.filter(user=request.user.storeuser, paid=False)
	return render(request, 'store/open_orders.html', { "open_orders": open_orders })

def order_edit(request, order_id):
	try:
		order_id = int(order_id)
	except ValueError:
		raise Http404()

	if request.method == 'POST':

		current_order = Order.objects.get(pk=order_id)
		form = OrderForm(request.POST, instance=current_order)

		if form.is_valid():
			form.save()
			return HttpResponseRedirect('/orders/')

	order = get_object_or_404(Order, pk=order_id)

	args = {}
	args.update(csrf(request))

	args['form'] = OrderForm(instance=order)
	args['order'] = order
	return render(request, 'store/order_edit.html', args)

def user_edit(request, user_id):
    try:
        user_id = int(user_id)
    except ValueError:
        raise Http404()

    if request.method == 'POST':
        auth_user = User.objects.get(id=user_id)
        form1 = UserForm(request.POST, instance=auth_user)
        form2 = StoreUserForm(request.POST, instance=auth_user.storeuser)
        if form1.is_valid() * form2.is_valid():
            form1.save()
            form2.save()
            return HttpResponseRedirect('/accounts/')

    current_user = get_object_or_404(User, id=user_id)
    args = {}
    args.update(csrf(request))
    args['form1'] = UserForm(instance=current_user)
    args['form2'] = StoreUserForm(instance=current_user.storeuser)
    args['user_id'] = user_id

    return render(request, 'store/user_edit.html', args)

def user_new(request):
	args = {}
	args.update(csrf(request))

	args['form'] = UserForm()
	args['user_info'] = StoreUserForm()
	args['new'] = True

	return render(request, 'store/register.html', args)
