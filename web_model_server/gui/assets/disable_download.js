document.addEventListener('contextmenu', function(e) {
    var el = e.target;
    if (el.tagName.toLowerCase() === 'video' || 
        el.tagName.toLowerCase() === 'img') {
    e.preventDefault();
    }
}, false);