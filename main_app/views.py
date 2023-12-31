from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum, Case, When, DecimalField, F, Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.admin.widgets import AdminDateWidget
from django.http import JsonResponse
from datetime import timedelta, date


from .models import Account, Transaction, Category, ChildTransaction


def home(request):
    # Calculate the total balance of all accounts
    # Get user accounts

    context = {}

    if request.user.is_authenticated:
        accounts = Account.objects.filter(user=request.user)
        # get balances
        account_balances = [account.calculate_account_balance() for account in accounts]
        # total_balance
        total_balance = sum(account_balances)

        # Retrieve all transactions ordered by timestamp
        transactions = Transaction.objects.filter(account__user=request.user).order_by('-date')
        childtransactions = []
        for transaction in transactions:
            childtransactions.extend(transaction.childtransactions.all())
        childtransactions = sorted(childtransactions, key=lambda x: x.date ) 
        running_balance = 0
        first_negative_transaction_id = -1
        for idx, el in enumerate(childtransactions):
            if el.transaction_type == "credit":
                running_balance = running_balance + el.amount
            else:
                running_balance = running_balance - el.amount
            el.transaction_number = idx
            el.running_balance = running_balance
            if running_balance < 0 and first_negative_transaction_id == -1:
                first_negative_transaction_id = idx-1

        context = {
            'total_balance': total_balance,
            'transactions': childtransactions,
            'first_negative_transaction_id': first_negative_transaction_id,
        }
    return render(request, "home.html", context)


class AccountCreate(LoginRequiredMixin , CreateView):
    model = Account
    fields = "__all__"

    def get_initial(self):
        initial = super(AccountCreate, self).get_initial()
        initial['user'] = self.request.user
        return initial



class AccountUpdate(LoginRequiredMixin, UserPassesTestMixin,UpdateView):
    model = Account
    fields = ['name']

    def test_func(self):
        account = self.get_object()
        return self.request.user == account.user


class AccountDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Account
    success_url = "/"

    def test_func(self):
        account = get_object_or_404(Account, id=self.kwargs['pk'])
        return self.request.user == account.user


class AccountDetail(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Account

    def test_func(self):
        account = get_object_or_404(Account, id=self.kwargs['pk'])
        return self.request.user == account.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Retrieve the list of transactions for the account
        account = self.object
        transaction_list = Transaction.objects.filter(account=account)
        childtransactions = []
        for transaction in transaction_list:
            childtransactions.extend(transaction.childtransactions.all())
            
        childtransactions = sorted(childtransactions, key=lambda x: x.date ) 

        context['transaction_list'] = childtransactions
        return context


class AccountList(LoginRequiredMixin, ListView):
    model = Account
    fields = "__all__"

    def get_queryset(self):
        # Only include accounts owned by the current user
        return Account.objects.filter(user=self.request.user)


class TransactionCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Transaction
    fields = "__all__"

    def test_func(self):
        account = Account.objects.get(id=self.kwargs['account_id'])
        return self.request.user == account.user

    def get_initial(self):
        initial = super().get_initial()
        account_id = self.kwargs.get('account_id')
        account = Account.objects.get(id=account_id)
        initial['account'] = Account.objects.get(id=account_id)
        initial['transaction_type'] = "debit"
        initial['repeats'] = "once"
        self.success_url = f"/accounts/{account_id}/"
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account_id = self.kwargs['account_id']
        context['account_id'] = account_id
        context['account'] = Account.objects.get(id=account_id)
        return context

    def get_form(self, form_class=None):
        form = super(TransactionCreate, self).get_form(form_class)
        # date field will otherwise be rendered as a regular input for no reason
        form.fields["date"].widget = AdminDateWidget(attrs={"type": "date"})
        return form


class TransactionUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Transaction
    fields = "__all__"
    success_url = "/"

    def test_func(self):
        account = Account.objects.get(id=self.kwargs['account_id'])
        return self.request.user == account.user

class TransactionDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Transaction
    success_url = "/"

    def test_func(self):
        account = Account.objects.get(id=self.kwargs['account_id'])
        return self.request.user == account.user

class TransactionDetail(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Transaction

    def test_func(self):
        account = Account.objects.get(id=self.kwargs['account_id'])
        return self.request.user == account.user

class TransactionList(LoginRequiredMixin,UserPassesTestMixin, ListView):
    model = Transaction
    fields = "__all__"

    def test_func(self):
        account = get_object_or_404(Account, id=self.kwargs['pk'])
        return self.request.user == account.user

def signup(request):
    error_message = ''
    if request.method == 'POST':
    # This is how to create a 'user' form object
    # that includes the data from the browser
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # This will add the user to the database
            user = form.save()
            # This is how we log a user in via code
            login(request, user)
            return redirect('/')
        else:
            error_message = 'Invalid sign up - try again'
     # A bad POST or a GET request, so render signup.html with an empty form form = UserCreationForm()
    form = UserCreationForm()
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)


class CategoryList(LoginRequiredMixin, ListView):
    ## will need to be protected by user
    model = Category
    fields = ['name']

    def get_queryset(self):
        # Only include categories created by the current user
        return Category.objects.filter(user=self.request.user)


class CategoryCreate(LoginRequiredMixin, CreateView):
    model = Category
    fields = "__all__"
    success_url = '/categories'

    def get_initial(self):
        initial = super(CategoryCreate, self).get_initial()
        initial['user'] = self.request.user
        return initial


class CategoryDetail(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Category

    def test_func(self):
        category = get_object_or_404(Category, id=self.kwargs['pk'])
        return self.request.user == category.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Retrieve the list of transactions for the account
        category = self.object
        transaction_list = Transaction.objects.filter(category=category)

        context['transaction_list'] = transaction_list
        return context


class CategoryDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Category
    success_url = "/categories"

    def test_func(self):
        category = get_object_or_404(Category, id=self.kwargs['pk'])
        return self.request.user == category.user

class CategoryUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Category
    fields = ['name']
    success_url = "/categories"

    def test_func(self):
        category = get_object_or_404(Category, id=self.kwargs['pk'])
        return self.request.user == category.user




def PieCharts(request):

    days = request.GET.get('days', None)  # Get the days parameter from the URL, default to None if not provided

    categories = Category.objects.filter(user=request.user)

    if days:
        start_date = date.today() - timedelta(days=int(days))
        categories = categories.filter(childtransaction__date__gte=start_date)

    
    if request.user.is_authenticated:
        # get expenses
        expenses = categories.annotate(
            total=Sum(
                Case(
                    When(childtransaction__transaction_type='debit', then='childtransaction__amount'),
                    default=0,
                    output_field=DecimalField()
                )
            )
        )
        # get income
        incomes = categories.annotate(
            total=Sum(
                Case(
                    When(childtransaction__transaction_type='credit', then='childtransaction__amount'),
                    default=0,
                    output_field=DecimalField()
                )
            )
        )

    # Convert the queryset into a list of dictionaries
    expenses = [{'category': expense.name, 'total': abs(expense.total)} for expense in expenses if expense.total]
    incomes = [{'category': income.name, 'total': abs(income.total)} for income in incomes if income.total]

    return JsonResponse({'expenses': expenses, 'income': incomes})



class ChildTransactionUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ChildTransaction
    fields = "__all__"
    success_url = "/"

    def test_func(self):
        account = Account.objects.get(id=self.kwargs['account_id'])
        return self.request.user == account.user

class ChildTransactionDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ChildTransaction
    success_url = "/"

    def test_func(self):
        account = Account.objects.get(id=self.kwargs['account_id'])
        return self.request.user == account.user
