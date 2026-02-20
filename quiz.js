// ============================================
// 全局变量
// ============================================
let chapters = [];          // 所有章节信息
let currentQuestions = [];  // 当前题目
let currentQuestionIndex = 0;
let userAnswers = [];
let currentChapterId = null;
let timerInterval;
let timeRemaining = 20 * 60; // 20分钟

// ============================================
// 1. 加载章节配置
// ============================================
async function loadChaptersConfig() {
    try {
        const response = await fetch('chapters.json');
        const data = await response.json();
        chapters = data.chapters;
        
        // 渲染章节选择界面
        renderChapterCards();
        
        return true;
    } catch (error) {
        console.error('加载章节配置失败:', error);
        alert('无法加载章节列表，请检查 chapters.json 文件是否存在');
        return false;
    }
}

// ============================================
// 2. 渲染章节卡片
// ============================================
function renderChapterCards() {
    const chapterGrid = document.getElementById('chapterGrid');
    chapterGrid.innerHTML = '';
    
    chapters.forEach(chapter => {
        const card = document.createElement('div');
        card.className = 'chapter-card';
        card.onclick = () => startQuiz(chapter.id);
        
        card.innerHTML = `
            <div class="chapter-badge">${chapter.week}</div>
            <h3>${chapter.title}</h3>
            <p class="chapter-meta">
                <span class="instructor">👨‍🏫 ${chapter.instructor}</span>
                <span class="date">📅 ${chapter.date}</span>
            </p>
            <p class="chapter-desc">${chapter.description}</p>
            <span class="question-count">📝 ${chapter.questionCount} 题</span>
        `;
        
        chapterGrid.appendChild(card);
    });
    
    // 添加"全部章节"卡片
    const allCard = document.createElement('div');
    allCard.className = 'chapter-card all-chapters';
    allCard.onclick = () => startQuiz('all');
    
    allCard.innerHTML = `
        <div class="chapter-badge">🎯</div>
        <h3>全部章节</h3>
        <p class="chapter-meta">
            <span class="instructor">综合练习</span>
            <span class="date">All Weeks</span>
        </p>
        <p class="chapter-desc">随机抽取所有章节题目</p>
        <span class="question-count">📝 50 题</span>
    `;
    
    chapterGrid.appendChild(allCard);
}

// ============================================
// 3. 开始测验
// ============================================
async function startQuiz(chapterId) {
    currentChapterId = chapterId;
    
    // 显示加载动画
    document.getElementById('chapterSelect').classList.add('hidden');
    document.getElementById('loading').classList.remove('hidden');
    
    const success = await loadQuestions(chapterId);
    
    if (success) {
        currentQuestionIndex = 0;
        userAnswers = new Array(currentQuestions.length).fill(null);
        
        // 启动计时器
        startTimer();
        
        // 显示测验界面
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('quizContainer').classList.remove('hidden');
        
        // 显示第一题
        showQuestion(0);
    } else {
        // 加载失败，返回章节选择
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('chapterSelect').classList.remove('hidden');
    }
}

// ============================================
// 4. 加载题目
// ============================================
async function loadQuestions(chapterId) {
    try {
        if (chapterId === 'all') {
            // 加载所有章节的题目
            const allQuestions = [];
            
            for (const chapter of chapters) {
                const questions = await loadChapterQuestions(chapter.fileName);
                allQuestions.push(...questions);
            }
            
            // 随机抽取50题
            currentQuestions = getRandomItems(allQuestions, 50);
        } else {
            // 加载单个章节
            const chapter = chapters.find(c => c.id === chapterId);
            
            if (!chapter) {
                throw new Error(`未找到章节: ${chapterId}`);
            }
            
            currentQuestions = await loadChapterQuestions(chapter.fileName);
        }
        
        // 随机化题目顺序
        currentQuestions = shuffleArray(currentQuestions);
        
        return true;
    } catch (error) {
        console.error('加载题目失败:', error);
        alert(`无法加载题目数据：${error.message}`);
        return false;
    }
}

// ============================================
// 5. 加载单个章节的题目
// ============================================
async function loadChapterQuestions(fileName) {
    try {
        const response = await fetch(`data/${fileName}`);
        const data = await response.json();
        return data.questions || data;
    } catch (error) {
        console.error(`加载 ${fileName} 失败:`, error);
        throw new Error(`文件 ${fileName} 不存在或格式错误`);
    }
}

// ============================================
// 6. 显示题目
// ============================================
function showQuestion(index) {
    if (index < 0 || index >= currentQuestions.length) {
        console.error('题目索引超出范围:', index);
        return;
    }

    const question = currentQuestions[index];
    
    // 更新题号显示
    document.getElementById('currentQuestion').textContent = index + 1;
    document.getElementById('totalQuestions').textContent = currentQuestions.length;
    
    // 更新进度条
    const progress = ((index + 1) / currentQuestions.length) * 100;
    document.getElementById('progressFill').style.width = progress + '%';
    
    // 显示题目文本
    document.getElementById('questionText').textContent = question.question;
    
    // 渲染选项
    const optionsContainer = document.getElementById('optionsContainer');
    optionsContainer.innerHTML = '';
    
    question.options.forEach((option, optionIndex) => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'option';
        optionDiv.onclick = () => selectOption(index, optionIndex);
        
        // 如果已经选择过，高亮显示
        if (userAnswers[index] === optionIndex) {
            optionDiv.classList.add('selected');
        }
        
        optionDiv.innerHTML = `
            <div class="option-label">${String.fromCharCode(65 + optionIndex)}</div>
            <div class="option-text">${option.text}</div>
        `;
        
        optionsContainer.appendChild(optionDiv);
    });
    
    // 更新按钮状态
    document.getElementById('prevBtn').disabled = (index === 0);
    document.getElementById('nextBtn').style.display = (index === currentQuestions.length - 1) ? 'none' : 'inline-block';
    document.getElementById('submitBtn').style.display = (index === currentQuestions.length - 1) ? 'inline-block' : 'none';
}

// ============================================
// 7. 选择答案
// ============================================
function selectOption(questionIndex, optionIndex) {
    userAnswers[questionIndex] = optionIndex;
    
    // 更新选项的视觉状态
    const options = document.querySelectorAll('.option');
    options.forEach((opt, idx) => {
        if (idx === optionIndex) {
            opt.classList.add('selected');
        } else {
            opt.classList.remove('selected');
        }
    });
}

// ============================================
// 8. 上一题
// ============================================
document.getElementById('prevBtn').addEventListener('click', function() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        showQuestion(currentQuestionIndex);
    }
});

// ============================================
// 9. 下一题
// ============================================
document.getElementById('nextBtn').addEventListener('click', function() {
    if (currentQuestionIndex < currentQuestions.length - 1) {
        currentQuestionIndex++;
        showQuestion(currentQuestionIndex);
    }
});

// ============================================
// 10. 提交测验
// ============================================
document.getElementById('submitBtn').addEventListener('click', function() {
    // 检查是否有未作答的题目
    const unanswered = userAnswers.filter(answer => answer === null).length;
    
    if (unanswered > 0) {
        const confirmSubmit = confirm(`还有 ${unanswered} 题未作答，确定要提交吗？`);
        if (!confirmSubmit) return;
    }
    
    submitQuiz();
});

function submitQuiz() {
    // 停止计时器
    if (timerInterval) clearInterval(timerInterval);
    
    // 计算得分
    let correctCount = 0;
    currentQuestions.forEach((question, index) => {
        const userAnswer = userAnswers[index];
        if (userAnswer !== null && question.options[userAnswer].isCorrect) {
            correctCount++;
        }
    });
    
    // 显示结果
    showResults(correctCount);
}

// ============================================
// 11. 显示结果
// ============================================
function showResults(correctCount) {
    const totalQuestions = currentQuestions.length;
    const incorrectCount = totalQuestions - correctCount;
    const percentage = Math.round((correctCount / totalQuestions) * 100);
    
    // 隐藏测验界面，显示结果界面
    document.getElementById('quizContainer').classList.add('hidden');
    document.getElementById('resultsContainer').classList.remove('hidden');
    
    // 更新统计数据
    document.getElementById('scoreDisplay').textContent = `${correctCount}/${totalQuestions}`;
    document.getElementById('scorePercentage').textContent = `${percentage}%`;
    document.getElementById('correctCount').textContent = correctCount;
    document.getElementById('incorrectCount').textContent = incorrectCount;
    document.getElementById('totalCount').textContent = totalQuestions;
    
    // 渲染详细结果
    const resultsContainer = document.getElementById('questionsResults');
    resultsContainer.innerHTML = '';
    
    currentQuestions.forEach((question, index) => {
        const userAnswer = userAnswers[index];
        const correctAnswerIndex = question.options.findIndex(opt => opt.isCorrect);
        const isCorrect = userAnswer === correctAnswerIndex;
        
        const resultCard = document.createElement('div');
        resultCard.className = 'result-card';
        
        resultCard.innerHTML = `
            <div class="result-card-header ${isCorrect ? 'correct' : 'incorrect'}">
                <span class="result-number">第 ${index + 1} 题</span>
                <span class="result-status">${isCorrect ? '✓ 正确' : '✗ 错误'}</span>
            </div>
            <div class="result-question">${question.question}</div>
            ${userAnswer !== null ? `
                <div class="result-answer ${isCorrect ? 'correct' : 'incorrect'}">
                    你的答案：${question.options[userAnswer].text}
                </div>
            ` : '<div class="result-answer unanswered">未作答</div>'}
            ${!isCorrect ? `
                <div class="result-answer correct">
                    正确答案：${question.options[correctAnswerIndex].text}
                </div>
            ` : ''}
            <div class="result-explanation">
                <strong>解析：</strong>${question.options[correctAnswerIndex].reason || question.explanation || ''}
            </div>
        `;
        
        resultsContainer.appendChild(resultCard);
    });
}
// ============================================
// 工具函数
// ============================================

// 随机化数组
function shuffleArray(array) {
    const newArray = [...array];
    for (let i = newArray.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
    }
    return newArray;
}

// 从数组中随机抽取指定数量的元素
function getRandomItems(array, count) {
    const shuffled = shuffleArray(array);
    return shuffled.slice(0, count);
}

// 启动计时器
function startTimer() {
    timeRemaining = 20 * 60; // 重置为20分钟
    updateTimerDisplay();
    
    if (timerInterval) clearInterval(timerInterval);
    
    timerInterval = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();
        
        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            submitQuiz();
        }
    }, 1000);
}

// 更新计时器显示
function updateTimerDisplay() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    document.getElementById('timer').textContent = 
        `⏱️ 剩余时间: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// ... (其他测验逻辑函数 - showQuestion, nextQuestion, prevQuestion, submitQuiz, showResults 等)
// 这些函数与之前提供的版本相同