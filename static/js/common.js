/**
 * 中科恒泰隧道炉 - 通用JS工具
 */
function get(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.onload = function() {
        if (xhr.status === 200) callback(JSON.parse(xhr.responseText));
    };
    xhr.send();
}

function post(url, data, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        if (xhr.status === 200 && callback) callback(JSON.parse(xhr.responseText));
    };
    xhr.send(JSON.stringify(data));
}

function postForm(url, formData, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.onload = function() {
        if (xhr.status === 200 && callback) callback(JSON.parse(xhr.responseText));
    };
    xhr.send(new URLSearchParams(formData));
}

function formatTime(d) {
    if (!d) return '';
    var dt = new Date(d);
    return dt.toLocaleString('zh-CN', { hour12: false });
}

function getCookie(name) {
    var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
}
