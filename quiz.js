let currentQuestions = [];
let currentQuestionIndex = 0;
let userAnswers = [];

// ============================================
// 1. 从 JSON 文件加载题目
// ============================================
async function loadQuestions(week) {
    try {
        let response;
        
        if (week === 'all') {
            // 加载所有章节
            const weeks = ['week1', 'week2', 'week3', 'week4', 'week5'];
            const promises = weeks.map(w => fetch(`data/${w}.json`));
            const results = await Promise.all(promises);
            const allData = await Promise.all(results.map(r => r.json()));
            
            // 合并所有题目
            currentQuestions = [];
            allData.forEach(data => {
                currentQuestions = currentQuestions.concat(data.questions);
            });
        } else {
            // 加载单个章节
            response = await fetch(`data/${week}.json`);
            const data = await response.json();
            currentQuestions = data.questions;
        }
        
        // 随机化题目顺序
        currentQuestions = shuffleArray(currentQuestions);
        
        return true;
    } catch (error) {
        console.error('加载题目失败:', error);
        alert('无法加载题目数据，请检查网络连接或文件路径');
        return false;
    }
}

// ============================================
// 2. 开始测验
// ============================================
async function startQuiz(week) {
    const success = await loadQuestions(week);
    
    if (success) {
        currentQuestionIndex = 0;
        userAnswers = new Array(currentQuestions.length).fill(null);
        
        // 切换到测验界面
        document.getElementById('chapterSelect').classList.add('hidden');
        document.getElementById('quizContainer').classList.remove('hidden');
        
        // 显示第一题
        showQuestion(0);
    }
}

// ============================================
// 3. 随机化函数
// ============================================
function shuffleArray(array) {
    const newArray = [...array];
    for (let i = newArray.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
    }
    return newArray;
}

// ============================================
// 4. 显示题目
// ============================================
function showQuestion(index) {
    const question = currentQuestions[index];
    
    // 随机化选项
    const shuffledOptions = shuffleArray(question.options);
    question.shuffledOptions = shuffledOptions;
    
    // 渲染题目...
}

// ... 其他测验逻辑（与之前相同）