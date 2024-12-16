from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login,authenticate
from django.shortcuts import render, redirect
from .forms import PedidoForm
from .models import Producto, Categoria, Pedido,Venta
from django.contrib.auth import logout
from .forms import CustomUserCreationForm
from django.contrib.auth.views import LoginView
from .forms import LoginForm
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.exceptions import ValidationError




def lista_productos(request):
    productos = Producto.objects.all()
    categorias = Categoria.objects.all()
    return render(request, 'tienda/lista_productos.html', {
        'productos': productos,
        'categorias': categorias
    })


def productos_por_categoria(request, categoria_id):
    # Obtener la categoría, o 404 si no se encuentra
    categoria = get_object_or_404(Categoria, id=categoria_id)
    
    # Obtener los productos de esa categoría
    productos = Producto.objects.filter(categoria=categoria)
    
    # Obtener todas las categorías para mostrarlas en el menú
    categorias = Categoria.objects.all()
    
    # Pasar los productos y las categorías al template
    return render(request, 'tienda/lista_productos.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria': categoria
    })
    



def agregar_al_carrito(request, producto_id):
    try:
        # Obtener el producto desde la base de datos
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return redirect('lista_productos')

    # Obtener el carrito desde la sesión (o uno vacío si no existe)
    carrito = request.session.get('carrito', {})

    # Convertir el precio de Decimal a float
    precio_producto = float(producto.precio)

    # Si el producto ya está en el carrito, incrementar su cantidad
    if str(producto.id) in carrito:
        carrito[str(producto.id)]['cantidad'] += 1
    else:
        # Si no está en el carrito, agregarlo
        carrito[str(producto.id)] = {
            'titulo': producto.titulo,
            'precio': precio_producto,
            'cantidad': 1
        }
    if producto.cantidad <= 0:
        messages.error(request, "Este producto no tiene stock disponible.")
        return redirect('lista_productos')  # Cambia esto a la URL adecuada

    # Guardar el carrito actualizado en la sesión
    request.session['carrito'] = carrito

    # Calcular el total de productos en el carrito (suma de todas las cantidades)
    total_productos = sum(item['cantidad'] for item in carrito.values())

    # Agregar el total de productos al contexto de la sesión
    request.session['total_productos'] = total_productos

    # Mensaje de éxito
    messages.success(request, f'El producto "{producto.titulo}" se ha añadido al carrito.')

    # Redirigir al usuario a la página anterior
    return redirect(request.META.get('HTTP_REFERER'))





def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    total_precio = 0
    total_productos = 0

    # Calcular el total de los precios y la cantidad de productos
    for producto_id, detalles in carrito.items():
        producto = Producto.objects.get(id=producto_id)  # Obtener el producto del carrito
        # Convertir el precio a float antes de calcular el total
        total_precio += float(producto.precio) * detalles['cantidad']  # Sumar el total por cantidad
        total_productos += detalles['cantidad']  # Sumar las cantidades de productos

    # Guardar el total de productos y el total de precios en la sesión (convertido a float)
    request.session['total_precio'] = total_precio
    request.session['total_productos'] = total_productos

    return render(request, 'tienda/carrito.html', {
        'carrito': carrito,
        'total_precio': total_precio,
        'total_productos': total_productos,
    })


def eliminar_del_carrito(request, producto_id):
    # Obtener el carrito desde la sesión
    carrito = request.session.get('carrito', {})

    # Verificar si el producto existe en el carrito
    if str(producto_id) in carrito:
        # Eliminar el producto del carrito
        del carrito[str(producto_id)]

        # Guardar el carrito actualizado en la sesión
        request.session['carrito'] = carrito

        # Calcular el total de productos en el carrito
        total_productos = sum(item['cantidad'] for item in carrito.values())
        request.session['total_productos'] = total_productos

        # Mensaje de éxito
        messages.success(request, f'El producto ha sido eliminado del carrito.')

    # Redirigir al carrito
    return redirect('ver_carrito')


#creacion de cuenta 

def register(request):
    data = {
        'form': CustomUserCreationForm()
    }

    if request.method == 'POST':
        user_creation_form = CustomUserCreationForm(data=request.POST)

        if user_creation_form.is_valid():
            user_creation_form.save()

            user = authenticate(username=user_creation_form.cleaned_data['username'], password=user_creation_form.cleaned_data['password1'])
            login(request, user)
            return redirect('lista_productos')
        else:
            data['form'] = user_creation_form

    return render(request, 'tienda/register.html', data)

@login_required
def realizar_pedido(request):
    carrito = request.session.get('carrito', {})

    # Verificar si el carrito está vacío
    if not carrito:
        messages.error(request, "El carrito está vacío.")
        return redirect('ver_carrito')  # Redirigir a la vista de carrito

    # Calcular el total
    total = sum((item['precio'] * item['cantidad']) * 1.19 for item in carrito.values())

    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            # Crear el pedido con estado 'pendiente'
            pedido = Pedido.objects.create(
                usuario=request.user,
                productos=carrito,  # Almacenar el carrito como un diccionario JSON
                total=total,
                direccion=form.cleaned_data['direccion'],
                codigo_postal=form.cleaned_data['codigo_postal'],
                telefono=form.cleaned_data['telefono'],
                email=form.cleaned_data['email'],
                estado='pendiente',  # El pedido se crea en estado pendiente
            )

            # Limpiar el carrito de la sesión
            request.session['carrito'] = {}
            request.session['total_productos'] = 0

            # Mensaje de éxito y redirección
            messages.success(request, "Tu pedido ha sido realizado con éxito.")
            return redirect('lista_productos')  # O a una página de confirmación
    else:
        form = PedidoForm()

    return render(request, 'tienda/realizar_pedido.html', {'form': form})
@login_required
def aceptar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    # Asegurarse de que el estado del pedido sea pendiente
    if pedido.estado != 'pendiente':
        return redirect('detalle_pedido', pedido_id=pedido.id)

    # Validar que haya suficiente stock para los productos
    for item in pedido.productos:
        producto = Producto.objects.get(id=item['id'])  # Asumiendo que el producto tiene un campo 'id'
        if producto.cantidad < item['cantidad']:
            raise ValidationError(f"No hay suficiente stock para el producto {producto.titulo}. Solo quedan {producto.cantidad} unidades.")

    # Actualizar el estado del pedido a 'aceptado' y disminuir el stock
    for item in pedido.productos:
        producto = Producto.objects.get(id=item['id'])
        producto.cantidad -= item['cantidad']  # Disminuir el stock
        producto.save()

    # Cambiar el estado del pedido a 'aceptado'
    pedido.estado = 'aceptado'
    pedido.save()

    # Redirigir a la página de detalles del pedido
    return redirect('detalle_pedido', pedido_id=pedido.id)

class CustomLoginView(LoginView):
    template_name = 'tienda/login.html'  # Plantilla para el formulario de login
    authentication_form = LoginForm  # Formulario personalizado (si tienes uno)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = "Iniciar sesión"
        return context

    def get_success_url(self):
        # Redirigir al panel de administración si el usuario es un administrador
        if self.request.user.is_staff:
            return '/panel_principal/'  # Redirigir a la página de administración de Django
        # Si no es admin, redirigir a la URL predeterminada
        return super().get_success_url()
    
def vista_pedidos(request):
    # Filtrar los pedidos con notificado=False
    pedidos_no_notificados = Pedido.objects.filter(notificado=False)

    # Verificar si hay pedidos no notificados
    hay_pedidos_no_notificados = pedidos_no_notificados.exists()

    # Pasar los datos a la plantilla
    return render(request, 'tienda/pedidos.html', {
        'pedidos_no_notificados': pedidos_no_notificados,
        'hay_pedidos_no_notificados': hay_pedidos_no_notificados,
    })    
    
    
@login_required
def notificaciones(request):
    pedidos = Pedido.objects.filter(usuario=request.user).exclude(estado='pendiente')
    return render(request, 'tienda/notificaciones.html', {'pedidos': pedidos})


def detalles_pedido(request, pedido_id):
    # Obtener el pedido con el ID dado
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Renderizar la plantilla con los datos del pedido
    return render(request, 'tienda/detalles_pedido.html', {'pedido': pedido})