// Add a confirmation dialog for deleting users or questions
document.addEventListener('DOMContentLoaded', function () {
    const deleteButtons = document.querySelectorAll('.btn-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            if (!confirm('Are you sure you want to delete this?')) {
                e.preventDefault();
            }
        });
    });
});

// Timer functionality for the quiz page
document.addEventListener('DOMContentLoaded', function () {
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        let timeLeft = sessionStorage.getItem('timeLeft') || 60;
        const quizForm = document.getElementById('quiz-form');

        const timer = setInterval(() => {
            timeLeft--;
            timerElement.textContent = timeLeft;
            sessionStorage.setItem('timeLeft', timeLeft);

            if (timeLeft <= 0) {
                clearInterval(timer);
                sessionStorage.removeItem('timeLeft');
                alert("Time's up! Submitting your quiz...");
                quizForm.submit();
            }
        }, 1000);

        quizForm.addEventListener('submit', () => {
            sessionStorage.removeItem('timeLeft');
        });
    }
});