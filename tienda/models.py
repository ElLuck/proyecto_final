from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    titulo = models.CharField(max_length=200)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField(default=0)  # Nuevo campo para la cantidad
    categoria = models.ForeignKey('Categoria', on_delete=models.CASCADE, related_name="productos")

    def clean(self):
        # Validación para que el precio no sea negativo
        if self.precio is not None and self.precio < 0:
            raise ValidationError("El precio no puede ser un número negativo.")
    def __str__(self):
        return self.titulo

class Galeria(models.Model):
    title=models.CharField(max_length=41)
    description=models.TextField()
    image=models.ImageField()
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name="Gallery"
        verbose_name_plural="Galleries"

    def __str__(self):
        return self.title  

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    productos = models.JSONField()  # O cualquier otra forma de almacenar productos
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    direccion = models.CharField(max_length=255, default='Unknown')
    codigo_postal = models.CharField(max_length=20, default='00000')
    telefono = models.CharField(max_length=20, default='0000000000')
    email = models.EmailField(default='unknown@example.com')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')  # Nuevo campo
    notificado = models.BooleanField(default=False)

    def __str__(self):
        return f"Pedido {self.id} - {self.usuario.username}"

    

class PedidoAceptado(Pedido):
    class Meta:
        proxy = True
        verbose_name = "Pedido Aceptado"
        verbose_name_plural = "Pedidos Aceptados"

class PedidoRechazado(Pedido):
    class Meta:
        proxy = True
        verbose_name = "Pedido Rechazado"
        verbose_name_plural = "Pedidos Rechazados"
        
class Venta(models.Model):
    producto = models.CharField(max_length=100)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Venta de {self.producto} - {self.total}"        