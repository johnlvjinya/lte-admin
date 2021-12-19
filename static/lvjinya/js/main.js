
function getQueryVariable(variable)
{
       var query = window.location.search.substring(1);
       var vars = query.split("&");
       for (var i=0;i<vars.length;i++) {
               var pair = vars[i].split("=");
               if(pair[0] == variable){return pair[1];}
       }
       return(false);
}

function selectChange(){
    console.log('...............selectChange()')
}

function showElementById(ElementId){
    var x=document.getElementById(ElementId);
    console.log(ElementId)
    x.style.display="block";
}

function hideElementById(ElementId){
    var x=document.getElementById(ElementId);
    console.log(ElementId)
    x.style.display="none";
}

function showDialogElementById(ElementId){
    var x=document.getElementById(ElementId);
    console.log('showDialogElementById===', ElementId)
    x.showModal();
}

function closeDialogElementById(ElementId){
    if (this.tr_id){
    var t_color=document.getElementById(this.tr_id);
        if (t_color){
            t_color.style.background='white';       
        }
    }
    var x=document.getElementById(ElementId);
    console.log('close...........', ElementId)
    x.close();
    // location.replace(location.href);
}

function openurl(url){
   var iWidth=900;                          //弹出窗口的宽度;
   var iHeight=900;                         //弹出窗口的高度;
   //获得窗口的垂直位置
   var iTop = (window.screen.availHeight - 30 - iHeight) / 2;
   //获得窗口的水平位置
   var iLeft = (window.screen.availWidth - 10 - iWidth) / 2;    
    myWindow=window.open(url,'newwindow','height=' + iHeight + ',,innerHeight=' + iHeight + ',width=' + iWidth + ',innerWidth=' + iWidth + ',top=' + iTop + ',left=' + iLeft + ',status=no,toolbar=no,menubar=no,location=no,resizable=no,scrollbars=0,titlebar=no');
    myWindow.focus();
}

function openurlfull(url){
   var iWidth=3000;                          //弹出窗口的宽度;
   var iHeight=1900;                         //弹出窗口的高度;
   //获得窗口的垂直位置
   var iTop = (window.screen.availHeight - 30 - iHeight) / 2;
   //获得窗口的水平位置
   var iLeft = (window.screen.availWidth - 10 - iWidth) / 2;    
    myWindow=window.open(url,'newwindow','height=' + iHeight + ',,innerHeight=' + iHeight + ',width=' + iWidth + ',innerWidth=' + iWidth + ',top=' + iTop + ',left=' + iLeft + ',status=no,toolbar=no,menubar=no,location=no,resizable=no,scrollbars=0,titlebar=no');
    myWindow.focus();

}