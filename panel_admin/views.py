from django.shortcuts import render, get_object_or_404, redirect
from tienda.models import Categoria, Producto, Pedido, Venta
from django.db import models  # Añadir esta importación
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
# Vista principal del panel
# Vista principal del panel
def panel_principal(request):
    total_categorias = Categoria.objects.count()
    total_productos = Producto.objects.count()
    total_pedidos = Pedido.objects.count()
    total_ventas = Venta.objects.aggregate(total=models.Sum('total'))['total'] or 0  # Total de ventas

    # Obtener productos para mostrarlos en el panel
    productos = Producto.objects.select_related('categoria').all()

    return render(request, 'panel_admin/panel_principal.html', {
        'total_categorias': total_categorias,
        'total_productos': total_productos,
        'total_pedidos': total_pedidos,
        'total_ventas': total_ventas,
        'productos': productos  # Pasar los productos al template
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

def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente.')
        return redirect('lista_productos_admin')
    return render(request, 'panel_admin/producto_confirm_delete.html', {'producto': producto})
