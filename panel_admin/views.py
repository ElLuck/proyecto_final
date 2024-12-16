from django.shortcuts import render, get_object_or_404, redirect
from tienda.models import Categoria, Producto, Pedido, Venta
from django.db import models
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from tienda.forms import ProductoForm
from xhtml2pdf import pisa
from datetime import datetime
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import get_template
from django.db.models.functions import TruncWeek
from django.template.loader import render_to_string

# Vista principal del panel
def panel_principal(request):
    total_categorias = Categoria.objects.count()
    total_productos = Producto.objects.count()
    total_pedidos = Pedido.objects.count()
    total_ventas = Venta.objects.aggregate(total=models.Sum('total'))['total'] or 0  # Total de ventas

    # Obtener el número de pedidos en cada estado
    pedidos_en_proceso = Pedido.objects.filter(estado='pendiente').count()
    pedidos_aceptados = Pedido.objects.filter(estado='aceptado').count()
    pedidos_rechazados = Pedido.objects.filter(estado='rechazado').count()

    # Obtener productos para mostrarlos en el panel
    productos = Producto.objects.select_related('categoria').all()

    return render(request, 'panel_admin/panel_principal.html', {
        'total_categorias': total_categorias,
        'total_productos': total_productos,
        'total_pedidos': total_pedidos,
        'total_ventas': total_ventas,
        'productos': productos,
        'pedidos_en_proceso': pedidos_en_proceso,
        'pedidos_aceptados': pedidos_aceptados,
        'pedidos_rechazados': pedidos_rechazados,
    })

# Gestión de categorías
def lista_categorias(request):
    categorias = Categoria.objects.all()
    return render(request, 'panel_admin/categoria_list.html', {'categorias': categorias})

def crear_categoria(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            Categoria.objects.create(nombre=nombre)
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('lista_categorias')
    return render(request, 'panel_admin/categoria_form.html')

# Gestión de productos
def lista_productos_admin(request):
    productos = Producto.objects.select_related('categoria').all()
    return render(request, 'panel_admin/producto_list.html', {'productos': productos})

def crear_producto(request):
    categorias = Categoria.objects.all()
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        precio = request.POST.get('precio')
        cantidad = request.POST.get('cantidad')
        categoria_id = request.POST.get('categoria')
        nueva_categoria = request.POST.get('nueva_categoria')

        # Si se ingresa una nueva categoría, la creamos
        if nueva_categoria:
            categoria, created = Categoria.objects.get_or_create(nombre=nueva_categoria)
        elif categoria_id:  # Si se seleccionó una categoría existente
            categoria = get_object_or_404(Categoria, id=categoria_id)
        else:
            categoria = None

        # Manejar la carga de la imagen
        imagen = request.FILES.get('imagen')
        if imagen:
            fs = FileSystemStorage()
            imagen_url = fs.save(imagen.name, imagen)
        
        # Crear el producto
        Producto.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            precio=precio,
            cantidad=cantidad,
            categoria=categoria,
            imagen=imagen_url if imagen else None  # Guardar la URL de la imagen si se sube una
        )

        messages.success(request, 'Producto creado exitosamente.')
        return redirect('lista_productos_admin')
    
    return render(request, 'panel_admin/producto_form.html', {'categorias': categorias})

@login_required
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    producto.delete()
    messages.success(request, f'El producto "{producto.titulo}" ha sido eliminado.')
    return redirect('lista_productos_admin')

def actualizar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        precio = request.POST.get('precio')
        cantidad = request.POST.get('cantidad')
        categoria_id = request.POST.get('categoria')
        nueva_categoria = request.POST.get('nueva_categoria')

        # Manejar la categoría seleccionada o nueva
        if nueva_categoria:
            categoria, created = Categoria.objects.get_or_create(nombre=nueva_categoria)
        else:
            categoria = get_object_or_404(Categoria, id=categoria_id)

        # Manejar la imagen
        imagen = request.FILES.get('imagen')
        if imagen:
            producto.imagen = imagen

        # Actualizar los datos del producto
        producto.titulo = titulo
        producto.descripcion = descripcion
        producto.precio = precio
        producto.cantidad = cantidad
        producto.categoria = categoria
        producto.save()

        messages.success(request, f"Producto '{producto.titulo}' actualizado correctamente.")
        return redirect('lista_productos_admin')

    return render(request, 'panel_admin/producto_form.html', {'producto': producto, 'categorias': categorias})


@login_required
def gestion_pedidos(request):
    pedidos_espera = Pedido.objects.filter(estado='pendiente')
    pedidos_aceptados = Pedido.objects.filter(estado='aceptado')
    pedidos_rechazados = Pedido.objects.filter(estado='rechazado')
    
    # Obtener todos los productos y crear un diccionario con el id como clave
    productos = Producto.objects.all()
    productos_dict = {producto.id: producto for producto in productos}

    return render(request, 'panel_admin/gestion_pedidos.html', {
        'pedidos_espera': pedidos_espera,
        'pedidos_aceptados': pedidos_aceptados,
        'pedidos_rechazados': pedidos_rechazados,
        'productos_dict': productos_dict,  # Pasar los productos al contexto
    })

@login_required
def aceptar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, estado='pendiente')
    if request.method == 'POST':
        pedido.estado = 'aceptado'
        pedido.save()
        messages.success(request, f"Pedido {pedido.id} aceptado exitosamente.")
    return redirect('gestion_pedidos')

@login_required
def rechazar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, estado='pendiente')
    if request.method == 'POST':
        pedido.estado = 'rechazado'
        pedido.save()
        messages.success(request, f"Pedido {pedido.id} rechazado exitosamente.")
    return redirect('gestion_pedidos')

def generar_pdf_ventas(request):
    # Filtramos los pedidos aceptados
    pedidos_aceptados = Pedido.objects.filter(estado='aceptado')

    # Sumar el total de todas las ventas
    total_ventas = pedidos_aceptados.aggregate(total=Sum('total'))['total'] or 0

    # Renderizar la plantilla HTML con las ventas
    html_string = render_to_string('panel_admin/ventas_resumen_pdf.html', {
        'pedidos_aceptados': pedidos_aceptados,
        'total_ventas': total_ventas,
    })

    # Generar el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="resumen_ventas.pdf"'
    
    # Convertir HTML a PDF usando xhtml2pdf
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF')
    return response