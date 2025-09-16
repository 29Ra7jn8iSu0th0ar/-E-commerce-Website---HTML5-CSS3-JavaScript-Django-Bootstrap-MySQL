import random
from .forms import ReviewForm
from django.urls import reverse
from django.contrib import messages
from accounts.models import Cart, CartItem
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product, SizeVariant, ProductReview, Wishlist

# Create your views here.

def get_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    sorted_size_variants = product.size_variant.all().order_by('size_name')
    related_products = list(product.category.products.filter(parent=None).exclude(uid=product.uid))

    # Review product view
    review = None
    if request.user.is_authenticated:
        try:
            review = ProductReview.objects.filter(product=product, user=request.user).first()
        except Exception as e:
            print("No reviews found for this product", str(e))
            messages.warning(request, "No reviews found for this product")

    rating_percentage = 0
    if product.reviews.exists():
        rating_percentage = (product.get_rating() / 5) * 100

    if request.method == 'POST' and request.user.is_authenticated:
        if review:
            # If review exists, update it
            review_form = ReviewForm(request.POST, instance=review)
        else:
            # Otherwise, create a new review
            review_form = ReviewForm(request.POST)

        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Review added successfully!")
            return redirect('get_product', slug=slug)
    else:
        review_form = ReviewForm()

    # Related product view
    if len(related_products) >= 4:
        related_products = random.sample(related_products, 4)

    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    context = {
        'product': product,
        'sorted_size_variants': sorted_size_variants,
        'related_products': related_products,
        'review_form': review_form,
        'rating_percentage': rating_percentage,
        'in_wishlist': in_wishlist,
    }

    if request.GET.get('size'):
        size = request.GET.get('size')
        price = product.get_product_price_by_size(size)
        context['selected_size'] = size
        context['updated_price'] = price

    return render(request, 'product/product.html', context=context)


# Product Review view
@login_required
def product_reviews(request):
    reviews = ProductReview.objects.filter(
        user=request.user).select_related('product').order_by('-date_added')
    return render(request, 'product/all_product_reviews.html', {'reviews': reviews})


# Edit Review view
@login_required
def edit_review(request, review_uid):
    review = ProductReview.objects.filter(uid=review_uid, user=request.user).first()
    if not review:
        return JsonResponse({"detail": "Review not found"}, status=404)
    
    if request.method == "POST":
        stars = request.POST.get("stars")
        content = request.POST.get("content")
        review.stars = stars
        review.content = content
        review.save()
        messages.success(request, "Your review has been updated successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return JsonResponse({"detail": "Invalid request"}, status=400)

# Like and Dislike review view
def like_review(request, review_uid):
    review = ProductReview.objects.filter(uid=review_uid).first()

    if request.user in review.likes.all():
        review.likes.remove(request.user)
    else:
        review.likes.add(request.user)
        review.dislikes.remove(request.user)
    return JsonResponse({'likes': review.like_count(), 'dislikes': review.dislike_count()})


def dislike_review(request, review_uid):
    review = ProductReview.objects.filter(uid=review_uid).first()

    if request.user in review.dislikes.all():
        review.dislikes.remove(request.user)
    else:
        review.dislikes.add(request.user)
        review.likes.remove(request.user)
    return JsonResponse({'likes': review.like_count(), 'dislikes': review.dislike_count()})


# delete review view
def delete_review(request, slug, review_uid):
    if not request.user.is_authenticated:
        messages.warning(request, "You need to be logged in to delete a review.")
        return redirect('login')

    review = ProductReview.objects.filter(uid=review_uid, product__slug=slug, user=request.user).first()
    
    if not review:
        messages.error(request, "Review not found.")
        return redirect('get_product', slug=slug)

    review.delete()
    messages.success(request, "Your review has been deleted.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# Add a product to Wishlist
@login_required
def add_to_wishlist(request, uid):
    variant = request.GET.get('size')
    if not variant:
        messages.warning(request, 'Please select a size variant before adding to the wishlist!')
        return redirect(request.META.get('HTTP_REFERER'))

    product = get_object_or_404(Product, uid=uid)
    size_variant = get_object_or_404(SizeVariant, size_name=variant)
    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user, product=product, size_variant=size_variant)

    if created:
        messages.success(request, "Product added to Wishlist!")

    return redirect(reverse('wishlist'))


# Remove product from wishlist
@login_required
def remove_from_wishlist(request, uid):
    product = get_object_or_404(Product, uid=uid)
    size_variant_name = request.GET.get('size')

    if size_variant_name:
        size_variant = get_object_or_404(SizeVariant, size_name=size_variant_name)
        Wishlist.objects.filter(
            user=request.user, product=product, size_variant=size_variant).delete()
    else:
        Wishlist.objects.filter(user=request.user, product=product).delete()

    messages.success(request, "Product removed from wishlist!")
    return redirect(reverse('wishlist'))


# Wishlist View
@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'product/wishlist.html', {'wishlist_items': wishlist_items})


# Move to cart functionality on wishlist page.
def move_to_cart(request, uid):
    product = get_object_or_404(Product, uid=uid)
    wishlist = Wishlist.objects.filter(user=request.user, product=product).first()

    if not wishlist:
        messages.error(request, "Item not found in wishlist.")
        return redirect('wishlist')

    size_variant = wishlist.size_variant
    wishlist.delete()

    cart, created = Cart.objects.get_or_create(user=request.user, is_paid=False)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, size_variant=size_variant)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, "Product moved to cart successfully!")
    return redirect('cart')

















# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.http import JsonResponse
# from django.db.models import Q
# from .models import Product, Review, Wishlist, Cart, CartItem, SizeVariant

# # ==========================
# # Product Detail Page
# # ==========================
# def get_product(request, slug):
#     product = get_object_or_404(Product, slug=slug)
#     reviews = Review.objects.filter(product=product).order_by("-created_at")

#     in_wishlist = False
#     if request.user.is_authenticated:
#         in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

#     return render(request, "product_detail.html", {
#         "product": product,
#         "reviews": reviews,
#         "in_wishlist": in_wishlist,
#     })


# # ==========================
# # Reviews
# # ==========================
# @login_required
# def add_review(request, slug):
#     product = get_object_or_404(Product, slug=slug)
#     if request.method == "POST":
#         rating = request.POST.get("rating")
#         comment = request.POST.get("comment")

#         if rating:
#             Review.objects.create(
#                 user=request.user,
#                 product=product,
#                 rating=rating,
#                 comment=comment
#             )
#             messages.success(request, "Review added successfully!")
#         else:
#             messages.error(request, "Rating is required to submit a review.")

#     return redirect("get_product", slug=slug)


# @login_required
# def delete_review(request, review_id):
#     review = get_object_or_404(Review, id=review_id, user=request.user)
#     review.delete()
#     messages.success(request, "Review deleted successfully!")
#     return redirect("get_product", slug=review.product.slug)


# # ==========================
# # Wishlist
# # ==========================
# @login_required
# def add_to_wishlist(request, slug):
#     product = get_object_or_404(Product, slug=slug)
#     Wishlist.objects.get_or_create(user=request.user, product=product)
#     messages.success(request, f"{product.product_name} added to wishlist!")
#     return redirect("get_product", slug=slug)


# @login_required
# def remove_from_wishlist(request, slug):
#     product = get_object_or_404(Product, slug=slug)
#     Wishlist.objects.filter(user=request.user, product=product).delete()
#     messages.success(request, f"{product.product_name} removed from wishlist!")
#     return redirect("get_product", slug=slug)


# # ==========================
# # Cart
# # ==========================
# @login_required
# def add_to_cart(request, slug):
#     product = get_object_or_404(Product, slug=slug)

#     # Check if size was provided
#     size_name = request.POST.get("size")
#     if not size_name:
#         messages.error(request, "Please select a size before adding to cart!")
#         return redirect("get_product", slug=slug)

#     # Validate size
#     try:
#         size_variant = SizeVariant.objects.get(size_name=size_name, product=product)
#     except SizeVariant.DoesNotExist:
#         messages.error(request, "Selected size is not available for this product.")
#         return redirect("get_product", slug=slug)

#     # Get or create a cart for the user
#     cart, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)

#     # Add or update cart item
#     cart_item, created = CartItem.objects.get_or_create(
#         cart=cart, product=product, size_variant=size_variant
#     )
#     if not created:
#         cart_item.quantity += 1
#         cart_item.save()

#     messages.success(request, f"{product.product_name} ({size_name}) added to your cart.")
#     return redirect("cart")


# @login_required
# def move_to_cart(request, slug):
#     product = get_object_or_404(Product, slug=slug)
#     Wishlist.objects.filter(user=request.user, product=product).delete()
#     return add_to_cart(request, slug)


# # ==========================
# # Search
# # ==========================
# def search_products(request):
#     query = request.GET.get("q")
#     results = []
#     if query:
#         results = Product.objects.filter(
#             Q(product_name__icontains=query) |
#             Q(description__icontains=query)
#         )
#     return render(request, "search_results.html", {"results": results, "query": query})
