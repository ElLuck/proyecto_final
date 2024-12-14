from django.shortcuts import render, get_object_or_404, redirect
from tienda.models import Categoria, Producto, Pedido, Venta
from django.db import models  # Añadir esta importación
from django.contrib import messages

# Vista principal del panel
def panel_principal(request):
    total_categorias = Categoria.objects.count()
    total_productos = Producto.objects.count()
    total_pedidos = Pedido.objects.count()
    total_ventas = Venta.objects.aggregate(total=models.Sum('total'))['total'] or 0  # Ahora 'models' está importado correctamente
    return render(request, 'panel_admin/panel_principal.html', {
        'total_categorias': total_categorias,
        'total_productos': total_productos,
        'total_pedidos': total_pedidos,
        'total_ventas': total_ventas,
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
        categoria = get_object_or_404(Categoria, id=categoria_id)
        Producto.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            precio=precio,
            cantidad=cantidad,
            categoria=categoria
        )
        messages.success(request, 'Producto creado exitosamente.')
        return redirect('lista_productos_admin')
    return render(request, 'panel_admin/producto_form.html', {'categorias': categorias})

def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente.')
        return redirect('lista_productos_admin')
    return render(request, 'panel_admin/producto_confirm_delete.html', {'producto': producto})
