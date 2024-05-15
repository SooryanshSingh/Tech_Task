
from django.db import models

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    option1 = models.CharField(max_length=100)
    option2 = models.CharField(max_length=100)
    option3 = models.CharField(max_length=100)
    option4 = models.CharField(max_length=100)
    correct_answer = models.CharField(max_length=100)

    def __str__(self):
        return self.question_text
	def create_hard_gk_questions():
    questions = [
        {
            'question_text': 'What is the capital of Australia?',
            'option1': 'Sydney',
            'option2': 'Melbourne',
            'option3': 'Canberra',
            'option4': 'Perth',
            'correct_answer': 'Canberra'
        },
        {
            'question_text': 'Who is the author of "War and Peace"?',
            'option1': 'Fyodor Dostoevsky',
            'option2': 'Leo Tolstoy',
            'option3': 'Charles Dickens',
            'option4': 'Jane Austen',
            'correct_answer': 'Leo Tolstoy'
        },
        {
            'question_text': 'Which planet is known as the "Red Planet"?',
            'option1': 'Venus',
            'option2': 'Mars',
            'option3': 'Jupiter',
            'option4': 'Saturn',
            'correct_answer': 'Mars'
        },
        {
            'question_text': 'What is the chemical symbol for gold?',
            'option1': 'Go',
            'option2': 'Au',
            'option3': 'Ag',
            'option4': 'G',
            'correct_answer': 'Au'
        },
        {
            'question_text': 'Who painted the Mona Lisa?',
            'option1': 'Leonardo da Vinci',
            'option2': 'Pablo Picasso',
            'option3': 'Vincent van Gogh',
            'option4': 'Michelangelo',
            'correct_answer': 'Leonardo da Vinci'
        },
        {
            'question_text': 'Which is the longest river in the world?',
            'option1': 'Nile',
            'option2': 'Amazon',
            'option3': 'Yangtze',
            'option4': 'Mississippi',
            'correct_answer': 'Nile'
        },
        {
            'question_text': 'Who wrote "To Kill a Mockingbird"?',
            'option1': 'Harper Lee',
            'option2': 'Mark Twain',
            'option3': 'Ernest Hemingway',
            'option4': 'J.K. Rowling',
            'correct_answer': 'Harper Lee'
        },
        {
            'question_text': 'Which is the smallest bone in the human body?',
            'option1': 'Femur',
            'option2': 'Tibia',
            'option3': 'Stapes',
            'option4': 'Fibula',
            'correct_answer': 'Stapes'
        },
        {
            'question_text': 'What is the tallest mountain in the world?',
            'option1': 'Mount Everest',
            'option2': 'K2',
            'option3': 'Kangchenjunga',
            'option4': 'Lhotse',
            'correct_answer': 'Mount Everest'
        },
        {
            'question_text': 'Who invented the telephone?',
            'option1': 'Thomas Edison',
            'option2': 'Alexander Graham Bell',
            'option3': 'Nikola Tesla',
            'option4': 'Guglielmo Marconi',
            'correct_answer': 'Alexander Graham Bell'
        },
    ]

    for q in questions:
        Question.objects.create(**q)
