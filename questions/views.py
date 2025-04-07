
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import Question, Answer
from .forms import QuestionForm, AnswerForm
from django.http import JsonResponse

class QuestionListView(ListView):
    model = Question
    template_name = 'questions/home.html'
    context_object_name = 'questions'
    ordering = ['-date_posted']
    paginate_by = 5

class QuestionDetailView(DetailView):
    model = Question
    template_name = 'questions/question_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answer_form'] = AnswerForm()
        context['answers'] = self.object.answers.all().order_by('-date_posted')
        return context

class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'questions/ask_question.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Your question has been posted!')
        return super().form_valid(form)

class QuestionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'questions/edit_question.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Your question has been updated!')
        return super().form_valid(form)
    
    def test_func(self):
        question = self.get_object()
        return self.request.user == question.author

class QuestionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Question
    template_name = 'questions/question_confirm_delete.html'
    success_url = '/'
    
    def test_func(self):
        question = self.get_object()
        return self.request.user == question.author

@login_required
def post_answer(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.author = request.user
            answer.save()
            messages.success(request, 'Your answer has been posted!')
            return redirect('question-detail', pk=question.pk)
    else:
        form = AnswerForm()
    return render(request, 'questions/question_detail.html', {'question': question, 'form': form})

@login_required
def like_answer(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        answer_id = request.POST.get('answer_id')
        answer = get_object_or_404(Answer, id=answer_id)
        
        if request.user in answer.likes.all():
            answer.likes.remove(request.user)
            liked = False
        else:
            answer.likes.add(request.user)
            liked = True
            
        return JsonResponse({'liked': liked, 'count': answer.total_likes()})
    return JsonResponse({'error': 'Invalid request'}, status=400)