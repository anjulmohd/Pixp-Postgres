from django.db import models
import datetime
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

from django.core.exceptions import ValidationError
# Create your models here.

class ProductManager(models.Manager):
    def active(self):
        return self.filter(is_blocked=False)

class Category(models.Model):
    name =models.CharField(max_length=50)
    image =models.ImageField(upload_to='uploads/category/')
    description = models.CharField(max_length=250,default ='',blank =True,null=True)
    is_sale = models.BooleanField(default=False)  # Mark category as on sale
    sale_percentage = models.DecimalField(default=0, max_digits=5, decimal_places=2)  # Discount percentage
    
    def __str__(self):
        return self.name
        
    

def generate_product_description(name, category):
    return (f"The {name} is a premium {category} designed for excellence. With top-tier quality, durability, and performance, it ensures an unmatched experience. Perfect for everyday use, it combines innovation and style, making it a must-have. Elevate your lifestyle with the {name}—crafted for perfection in every detail.")
    
class Product(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(default=0,decimal_places=2,max_digits=10,null=True, blank=True)
    price_initial = models.DecimalField(default=0,decimal_places=2,max_digits=10)
    category = models.ForeignKey(Category,on_delete=models.CASCADE,default =1)
    description = models.TextField(default='', blank=True, null=True)
    image =models.ImageField(upload_to='uploads/product/', max_length=255,null=True, blank=True)
    is_popular = models.BooleanField(default =False)
    is_featured = models.BooleanField(default =False)
    is_sale = models.BooleanField(default =False)
    sale_price =  models.DecimalField(default=0,decimal_places=2,max_digits=10)
    date = models.DateField(default = datetime.datetime.today)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=3)
    is_blocked = models.BooleanField(default = False)
    stock_quantity = models.IntegerField(default=10)
    base_product_detail = models.CharField(max_length=255,null=True, blank=True)
    def save(self, *args, **kwargs):
        """Update price based on discounts and ensure price updates properly."""
        
        # Ensure price_initial is always set
        if self.price_initial is None or self.price_initial == 0:
            self.price_initial = self.price  

        # Calculate discounted prices
        final_price, _ = self.calculate_final_price()
        
        # Assign the computed final price
        self.price = final_price  

        # Automatically generate a description if missing
        if not self.description:
            self.description = generate_product_description(self.name, self.category)

        super().save(*args, **kwargs)  # Save the model with updated values

        

    def category_discounted_price(self):
        """Calculate price after category discount."""
        if self.category.is_sale and self.category.sale_percentage > 0:
            discount = (self.price_initial * self.category.sale_percentage) / 100
            return self.price_initial - discount
        return self.price_initial
    
    def product_discounted_price(self):
        """Calculate price after product discount."""
        if self.is_sale:
            return self.sale_price
        return self.price_initial
    
    def calculate_final_price(self):
        """Determine final price based on the best discount available and return which discount was applied."""
        if not self.category.is_sale and not self.is_sale:
            return self.price_initial, "No Sale Applied"
        
        category_price = self.category_discounted_price() if self.category.is_sale else self.price_initial
        product_price = self.product_discounted_price() if self.is_sale else self.price_initial

        # Choose the lower price and determine which discount was applied
        if category_price < product_price:
            return category_price, "Category Discount Applied"
        elif product_price < category_price:
            return product_price, "Product Discount Applied"
        else:
            return product_price, "No Sale Applied"  # This happens if both are equal

    objects = ProductManager()

    def __str__(self):
        return f"name : {self.name}"
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/images/')
    description = models.CharField(max_length=255, blank=True, null=True)  # Optional field for image description

    def __str__(self):
        return f"{self.product.name} - {self.description}"
    

class ProductAttributes(models.Model):
    product = models.ForeignKey(Product, related_name='attributes', on_delete=models.CASCADE)
    material =  models.CharField(max_length=50, blank=True, null=True,default='plastic')
    connectivity = models.CharField(max_length=50, blank=True, null=True,default='wired connection')
    led_indicators = models.CharField(max_length=50, blank=True, null=True,default='led for battery level')
    portabilty =  models.CharField(max_length=50, blank=True, null=True,default='easy to carry')
    os_support = models.CharField(max_length=50, blank=True, null=True,default='Compatible with android,Linux,Windows,etc')
    
    touch_countrols =  models.CharField(max_length=50, blank=True, null=True,default='Advanced controls using touch screen integration')


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=100)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=10)
    price_initial = models.DecimalField(default=0, decimal_places=2, max_digits=10, null=True, blank=True)  # Editable if needed
    color = models.CharField(max_length=50, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    stock_quantity = models.IntegerField(default=10)
    image = models.ImageField(upload_to='uploads/product_variants/', null=True, blank=True)

    def save(self, *args, **kwargs):
        # Set the default price to the price of the associated product
        if not self.price:
            self.price = self.product.price  # Set the price of the variant to the product's price

        # Set price_initial only on creation (first save if not set already)
        if self.price_initial is None:  # Set only if price_initial is not set
            self.price_initial = self.price  # Set initial price on first creation

        super().save(*args, **kwargs)

    def __str__(self):
        return f"name:{self.name} - Related product name -{self.product.name}"

    

