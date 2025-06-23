// chat.js 负责用户消息与ChatGPT消息交互后的 WebUI 页面更新

// 获取状态栏和消息对话框的引用
const messageInput = document.getElementById('user_input');

// 历史记录
var totMsg = [];
var chatNow = 0;
var chatCnt = 0;
var timeWhenNew = "";
var deleteId = new Set();

window.onload = windowOnload;//加载页面触发事件
window.addEventListener("beforeunload", (event) => {
    console.log('关闭')
    clearChat();
    var res = [];
    for (const x of deleteId) {
        res[res.length] = x;
    }
    var data = new FormData();
    data.append('message', res);
    navigator.sendBeacon('/delete', data);
});

function windowOnload() {
    var rq = new XMLHttpRequest();
    rq.open('POST', '/getHistory', true);
    rq.setRequestHeader('Content-Type', 'application/json');
    rq.onreadystatechange = function() {
        if (rq.readyState === XMLHttpRequest.DONE && rq.status === 200) {
            console.log(rq.responseText)
            var docs = JSON.parse(rq.responseText);
            for(var i = 0; i < docs.length; i++) {
                newChat(docs[i]['time']);
            }
            newChat();
        }
    }
    console.log('11');
    rq.send();
}

// 发送消息到服务器
async function sendUserMessage() {
    const message = messageInput.value;

    // 检查用户输入是否为空
    if (!message.trim()) {
        console.log("User input is empty. Please enter a question.");
        return false;
    }
    console.log(message)
    addMessage(message ,'user');
    await llmMessage(message);
    messageInput.value = "";
    return true;
}

function newChat(time=null){
    clearChat();
    if (time == null) {
        var d = new Date();
        timeWhenNew = d.toLocaleString();
        time = timeWhenNew;
    }
    const chatList = document.getElementById('chat-list-history');
    const chat = document.createElement('div');
    const row = document.createElement('div');
    const col1 = document.createElement('button');
    const col2 = document.createElement('button');

    chat.className = "list-group-item list-group-item-action px-1"
    chat.id = chatCnt+1;
    

    row.className = "row mx-1";
    col1.className = "col-9 px-0 btn btn-light";
    col1.id = chatCnt+1;
    col1.setAttribute("onclick", "getHistory(this.id)");
    col1.innerHTML = time;

    col2.className = "col-3 px-0 btn btn-light"
    col2.id = chatCnt+1;
    col2.setAttribute("onclick", "deleteHistory(this.id)");
    col2.innerHTML = "delete";
    
    row.appendChild(col1);
    row.appendChild(col2);
    chat.appendChild(row);

    chatList.insertBefore(chat, chatList.firstChild);
    chatCnt++;
    chatNow = chatCnt
    totMsg.push([]);
}

function getHistory(id){
    clearChat();
    chatNow = id;
    var rq = new XMLHttpRequest();
    rq.open('POST', '/getHistory', true);
    rq.setRequestHeader('Content-Type', 'application/json');
    rq.onreadystatechange = function() {
        if (rq.readyState === XMLHttpRequest.DONE && rq.status === 200) {
            console.log(rq.responseText)
            var docs = JSON.parse(rq.responseText);
            var msgs = docs[id-1]['content'];
            totMsg[chatNow-1] = [];
            for(var i = 0; i < msgs.length; i++) {
                addMessage(msgs[i]['msg'], msgs[i]['role']);
            }
        }
    }
    var data = JSON.stringify({'message': id});
    console.log('11');
    rq.send(data);
}

function deleteHistory(id){
    const chatList = document.getElementById('chat-list-history');
    const chat = document.getElementById(id);
    chatList.removeChild(chat);
    deleteId.add(id);
    clearChat();
}

function saveChat(){
    var rq = new XMLHttpRequest();
    rq.open('POST', '/getHistory', false);
    rq.setRequestHeader('Content-Type', 'application/json');
    rq.onreadystatechange = function() {
        if (rq.readyState === XMLHttpRequest.DONE && rq.status === 200) {
            console.log(rq.responseText)
            var docs = JSON.parse(rq.responseText);
            if (chatNow > docs.length) docs[docs.length] = {'time': timeWhenNew, 'content': totMsg[chatNow-1]};
            else docs[chatNow-1]['content'] = totMsg[chatNow-1];
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/saveHistory', false);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (rq.readyState === XMLHttpRequest.DONE && rq.status === 200) {
                    console.log('保存成功')
                }
            }
            console.log('11');
            var data = JSON.stringify({'message': docs});
            xhr.send(data);
            
        }
    }
    console.log('11');
    rq.send();
}

function get_discuss_pre(){
    return new Promise((resolve) => {
        var rq = new XMLHttpRequest();
        rq.open('POST', '/discuss', true);
        rq.setRequestHeader('Content-Type', 'application/json');
        rq.onreadystatechange = function() {
            if (rq.readyState === XMLHttpRequest.DONE && rq.status === 200) {
                console.log('111')
                var docs = JSON.parse(rq.responseText);
                var pre = docs['pre'];
                console.log(pre);
                addMessage(pre,'server');
                return resolve();
            }
        }
        console.log('11');
        rq.send();
    })
}

function get_discuss_dn(){
    return new Promise((resolve) => {
        var rq = new XMLHttpRequest();
        rq.open('POST', '/discuss', true);
        rq.setRequestHeader('Content-Type', 'application/json');
        rq.onreadystatechange = function() {
            if (rq.readyState === XMLHttpRequest.DONE && rq.status === 200) {
                var docs = JSON.parse(rq.responseText);
                var doctor = docs['doctor'];
                var nutritionist = docs['nutritionist'];
                console.log(docs);
                addMessage(doctor,'server');
                addMessage(nutritionist, 'server');
                return resolve();
            }
        }
        console.log('11');
        rq.send();
    })
}

// 收到服务器消息
async function llmMessage(msg){
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var rsp = JSON.parse(xhr.responseText);
            if (rsp['answer'] == "over") {
                addMessage("医生讨论中，您的报告将稍后生成...", 'server')
                get_discuss_pre().then((res) => {
                    return get_discuss_dn();
                }).then((res) => {
                    return get_discuss_dn();
                }).then((res) => {
                    addLink();
                    saveChat();
                    // llmMessage("");
                })
            }
            else {
                rsp = rsp['answer'];
                addMessage(rsp,'server');
                saveChat();
            }
        }
    };
    var data = JSON.stringify({"message": msg});
    xhr.send(data);
}

// 格式化反馈的消息
function formartHtml(response) {
    return response
}


// 在页面加载时动态设置消息栏的高度
window.addEventListener('DOMContentLoaded', function() {
    adjustHeight('chatHistory', 127);
//    adjustHeight('messagelist', 169); // 填入其他div的id和对应的高度
});

// 在窗口大小改变时重新调整消息栏的高度
window.addEventListener('resize', function() {
adjustHeight('chatHistory', 127);
// adjustHeight('messagelist', 169); // 填入其他div的id和对应的高度
});

// 动态设置高度
function adjustHeight(elementId, offset) {
const element = document.getElementById(elementId);
const windowHeight = window.innerHeight;
const navbarHeight = document.querySelector('.navbar').offsetHeight;
const footerHeight = document.querySelector('.fixed-bottom').offsetHeight;
const newHeight = windowHeight - navbarHeight - footerHeight - offset;
element.style.height = `${newHeight}px`;
}

function addLink() {
    const messageBox = document.getElementById('chatHistory');

    // 创建新的服务器消息
    const messageElement = document.createElement('div');
    messageElement.className = 'user-message';

    // 创建新的服务器消息头像
    const avatarContainer = document.createElement('div');
    avatarContainer.className = 'avatar-container';
    // 设置服务器消息头像
    const avatar = document.createElement('img');
    avatar.className = 'avatar';
    var discordlogourl = 'https://cdn-icons-png.flaticon.com/512/9193/9193824.png';
    avatar.src = discordlogourl;
    
    avatarContainer.appendChild(avatar);

    // 创建新的服务器消息内容对象
    const messageContent = document.createElement('a');
    messageContent.className = 'message-content';
    messageContent.href = 'http://127.0.0.1:5000/show';
    messageContent.text = '点击查看详细报告（报告不会保存在历史记录中，如有需要建议自行保存）';

    // 将头像容器和消息内容容器追加到消息元素
    messageElement.appendChild(avatarContainer);
    messageElement.appendChild(messageContent);

    // 将消息元素追加到消息对话框
    messageBox.appendChild(messageElement);
}

// 添加消息到对话框
function addMessage(message, messageType) {
    console.log('addmessage');
    const messageBox = document.getElementById('chatHistory');
    if (['$START.', '$END.'].includes(message)) {
        // 控制状态栏和输入框状态
        if (message === '$START.'){
            set_user_input(true)
        }else{
            set_user_input(false)
        }
        console.log(message);
        return;
    }

    // 创建新的服务器消息
    const messageElement = document.createElement('div');
    messageElement.className = messageType === 'user' ? 'user-message' : 'server-message';

    // 创建新的服务器消息头像
    const avatarContainer = document.createElement('div');
    avatarContainer.className = 'avatar-container';
    // 设置服务器消息头像
    const avatar = document.createElement('img');
    avatar.className = 'avatar';
    var discordlogourl = 'https://cdn-icons-png.flaticon.com/512/4228/4228704.png';
    var chatgptlogourl = 'https://cdn-icons-png.flaticon.com/512/9193/9193824.png';
    avatar.src = messageType === 'user' ? discordlogourl : chatgptlogourl;
    
    avatarContainer.appendChild(avatar);

    // 创建新的服务器消息内容对象
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageHtml = formartHtml(message);
    messageContent.innerHTML = messageHtml;

    // 将头像容器和消息内容容器追加到消息元素
    messageElement.appendChild(avatarContainer);
    messageElement.appendChild(messageContent);

    // 将消息元素追加到消息对话框
    messageBox.appendChild(messageElement);
    console.log('addmessage');
    messageBox.scrollTop = messageBox.scrollHeight;

    totMsg[chatNow-1][totMsg[chatNow-1].length] = {'role': messageType, 'msg': message};
}

function set_user_input(status) {
    console.log('disabled user input state: ', status)
    document.getElementById('user_input').disabled = status;
    document.getElementById('user_input_but').disabled = status;
    document.getElementById('user_clear_but').disabled = status;
}

// Function to clear the chat history
function clearChat() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/clear', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            // 清空聊天历史
            document.getElementById('chatHistory').innerHTML = '';
            // 清空输入字段
            document.getElementById('user_input').value = '';
        }
    };
    var data = JSON.stringify({"message": "clear"});
    xhr.send(data); // 这里发送请求，请求成功之后会执行上面那段。send的内容是可以在后端获取的
}
