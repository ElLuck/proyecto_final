from django.shortcuts import render

def index(request):
    return render(request,'panel_admin/index.html')

def widgets(request):
    return render(request,'panel_admin/widgets.html')

def tables(request):
    return render(request,'panel_admin/tables.html')

def invoice(request):
    return render(request,'panel_admin/invoice.html')

def gallery(request):
    return render(request,'panel_admin/gallery.html')

def buttons(request):
    return render(request,'panel_admin/buttons.html')