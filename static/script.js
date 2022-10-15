var change_btn = document.getElementById("change_btn")

change_btn.addEventListener("click" , function(){
    var textares = document.querySelectorAll("textarea")
    var i = document.getElementById("from_lang").value
    var j = document.getElementById("to_lang").value
    var k = textares[0].innerHTML
    var m = textares[1].innerHTML
    if( i != "DETECT LANGUAGE"){ 
        console.log(j, i);
        document.getElementById("from_lang").value = j
        document.getElementById("to_lang").value = i
        textares[0].innerHTML = m
        textares[1].innerHTML = k
    }
})