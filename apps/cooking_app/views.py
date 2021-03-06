from django.shortcuts import render, redirect, reverse
from .models import User, Comment, Recipe, Ingredient, Measurement, Step, RecipePic, Rating, UserPic, Category
from django.contrib import messages
import datetime
from django.http import JsonResponse
from .forms import PicsForm
from django.db.models import Q


# Create your views here.
def login(request):
	if request.method == "POST":
		results = User.objects.LoginValidation(request.POST)
		if len(results[0])<1:
			request.session['id'] = results[1]
			request.session['user_level'] = results[2]
			return redirect(reverse('potluck:index'))
		else:
			for error in results:
				messages.error(request, error)
	return render(request, 'cooking_app/login.html')


def register(request):
	if request.method == "POST":
		results = User.objects.RegisterValidation(request.POST)
		if len(results[0])<1:
			request.session['id'] = results[1]
			request.session['user_level'] = results[2]
			return redirect(reverse('potluck:index'))
		else:
			for error in results:
				messages.error(request, error)
	return render(request, 'cooking_app/register.html')


def index(request):
	if 'id' not in request.session:
		return redirect(reverse('potluck:login'))
	context ={
		'user': User.objects.get(id=request.session['id']),
		'recipes': Recipe.objects.all().order_by('-updated_at'),
		'images': RecipePic.objects.all().order_by('-updated_at'),
	}
	return render(request, 'cooking_app/index.html', context)


def show_recipe(request, recipe_id):
	if 'id' not in request.session:
		return redirect(reverse('potluck:login'))

	if request.method == 'POST':

		post = Comment.objects.create(comment=request.POST['comment'], user=User.objects.get(id=request.session['id']), recipe=Recipe.objects.get(id=recipe_id))
	ratings = Rating.objects.filter(recipe=recipe_id)
	sum_rating = 0.
	if len(ratings)>0:
		for rating in ratings:
			sum_rating += rating.rating
		avg_rating = sum_rating / len(ratings)
	else:
		avg_rating = 'No ratings yet.'
	if len(RecipePic.objects.filter(recipe=Recipe.objects.get(id=recipe_id))) > 0:
		image = RecipePic.objects.get(recipe=Recipe.objects.get(id=recipe_id))
	else:
		image = []
	recipe = Recipe.objects.get(id=recipe_id)
	total_time_hour = recipe.prep_time_hour + recipe.cook_time_hour
	total_time_minute = recipe.prep_time_minute + recipe.cook_time_minute

	if len(Rating.objects.filter(user=request.session['id'], recipe=recipe_id))>0:
		rating = False
	else:
		rating = True

	context = {
		'user': User.objects.get(id=request.session['id']),
		'recipe': Recipe.objects.get(id=recipe_id),
		'steps': Step.objects.filter(recipe=Recipe.objects.get(id=recipe_id)).order_by('created_at'),
		'image': image,
		'avg_rating': avg_rating,
		'total_time_hour': total_time_hour,
		'total_time_minute': total_time_minute,
		'comments': Comment.objects.filter(recipe=Recipe.objects.get(id=recipe_id)),
		'images': RecipePic.objects.all(),
		'rating': rating,
		'selected_categories': Category.objects.filter(recipe=Recipe.objects.get(id=recipe_id)),
	}
	return render(request, 'cooking_app/show_recipe.html', context)


def add_recipe(request):
	if 'id' not in request.session:
		return redirect(reverse('potluck:login'))

	if request.method == 'POST': # if 'POST' we are trying to add something, else trying to display form to add
		if len(Recipe.objects.validateRecipe(request.POST))>0: #run validations. returns errors if failed
			return redirect(reverse('potluck:add_recipe'))
		#create the recipe if validations passed
		recipe = Recipe.objects.create(title=request.POST['title'], creator=User.objects.get(id=request.session['id']), description=request.POST['description'], prep_time_hour=request.POST['prep_time_hour'], prep_time_minute=request.POST['prep_time_minute'], cook_time_hour=request.POST['cook_time_hour'], cook_time_minute=request.POST['cook_time_minute'])
		Category.objects.addCategory(request.POST, recipe)
		#add image
		print request.FILES
		if 'image' in request.FILES:
			RecipePic.objects.create(title=request.POST['title'], image=request.FILES['image'], recipe=recipe)
			# RecipePic.objects.create(title=request.POST['title'], image=request.FILES['file'])
		#redirect to edit page so user can add steps to recipe
		return redirect(reverse('potluck:edit_recipe', kwargs={'recipe_id': recipe.id}))
	return render(request, 'cooking_app/add_recipe.html', {'user': User.objects.get(id=request.session['id']), 'categories': Category.objects.create_categories()})


def edit_recipe(request, recipe_id):
	if 'id' not in request.session:
		return redirect(reverse('potluck:login'))

	if request.method == 'POST': # if 'POST' we are trying to update recipe, else trying to display edit page
		print request.FILES
		# if 'image' in request.FILES:
		# 	RecipePic.objects.update(recipe_id, request.Files)
		if 'title' in request.POST:
			if len(Recipe.objects.validateRecipe(request.POST)) > 0: # run validations. returns errors if failed
				return redirect(reverse('potluck:edit_recipe'))
			else:
				Recipe.objects.update(request.POST, recipe_id) # passed validation, not update

	# test if there are any steps for this recipe and pass them if so
	if len(Step.objects.filter(recipe=Recipe.objects.get(id=recipe_id)))>0:
		steps = Step.objects.filter(recipe=Recipe.objects.get(id=recipe_id)).order_by('created_at')
		step_count = steps.count() + 1
	else: # otherwise, pass empty list rather than none (so traversing in the template doesnt cause an error)
		steps = []
		step_count = 1

	context = {
		'user': User.objects.get(id=request.session['id']),
		'recipe': Recipe.objects.get(id=recipe_id),
		'steps':steps,
		'step_count': step_count,
		'ingredients': Ingredient.objects.all().order_by('ingredient'),
		'measurements': Measurement.objects.all().order_by('measurement'),
		'images': RecipePic.objects.all(),
		'categories': Category.objects.all(),
		'selected_categories': Category.objects.filter(recipe=Recipe.objects.get(id=recipe_id)),
	}
	return render(request, 'cooking_app/edit_recipe.html', context)


def delete_recipe(request, recipe_id):
	if 'id' not in request.session:
		return redirect(reverse('potluck:login'))

	Recipe.objects.get(id=recipe_id).delete()
	return redirect('potluck:index')


def add_step(request):
	if 'id' not in request.session:
		return redirect(reverse('potluck:login'))

	step = Step.objects.add_step(request.POST) # runs code to validate step and return step after creation
	return redirect(reverse('potluck:edit_recipe', kwargs={'recipe_id': step.recipe.id}))


def update_step(request, step_id):
	if 'id' not in request.session:
		return redirect(reverse('potluck:login'))

	step = Step.objects.update_step(request.POST, step_id) # runs code to validate step and return step after update
	return redirect(reverse('potluck:edit_recipe', kwargs={'recipe_id': step.recipe.id}))


def delete_step(request, step_id):
	if 'id' not in request.session:
		return redirect(reverse('potluck:login'))

	Step.objects.get(id=step_id).delete()
	return JsonResponse({'to_delete': step_id})


def show_user(request, id):
	if 'id' not in request.session:
		return redirect(reverse('potluck:login'))

	if request.method == 'POST':
		if 'image' in request.FILES:
			user_pic = UserPic.objects.pic(request.POST, request.FILES, id)
	else:
		if len(UserPic.objects.filter(user=User.objects.get(id=id))) > 0:
			user_pic = UserPic.objects.get(user=User.objects.get(id=id))
		else:
			user_pic = ''

	context = {
		'self': User.objects.get(id=request.session['id']),
		'user': User.objects.get(id=id),
		'recipes': Recipe.objects.filter(creator=User.objects.get(id=id)),
		'saves': Recipe.objects.filter(user=User.objects.get(id=id)),
		'images': RecipePic.objects.all(),
		'user_pic': user_pic,
	}
	return render(request, 'cooking_app/show_user.html', context)


def logout(request):
	for key in request.session.keys():
		del request.session[key]
	return redirect(reverse('potluck:login'))


def add_rating(request, recipe_id):
	if 'id' not in request.session:
		return redirect(reverse('potluck:login'))

	user_id = request.session['id']
	Rating.objects.add_rating(recipe_id, user_id, request.POST)
	return redirect(reverse('potluck:show_recipe', kwargs={'recipe_id':recipe_id}))


def save_recipe(request, recipe_id):
	if 'id' not in request.session:
		return redirect(reverse('potluck:login'))

	user = User.objects.get(id=request.session['id'])
	recipe = Recipe.objects.get(id=recipe_id)
	recipe.user.add(user)
	recipe.save()
	return redirect(reverse('potluck:show_recipe', kwargs={'recipe_id':recipe_id}))


def search(request):
	if request.method == 'POST':
		if 'category' in request.POST:
			# results = Recipe.objects.filter()
			results = []
			search = ''
			category = Category.objects.get(id=request.POST['category'])
			results = Recipe.objects.filter(recipe_category=category)
		else:
			search = request.POST['search']
			if search == '':
				results = []
			else:
				results = Recipe.objects.filter(Q(title__icontains=search) | Q(description__icontains=search))
	else:
		results = []
		search = ''
	context = {
		'results': results,
		'images': RecipePic.objects.all(),
		'keyword': search,
		'user': User.objects.get(id=request.session['id']),
		'categories': Category.objects.all(),
	}
	return render(request, 'cooking_app/search.html', context)










#
