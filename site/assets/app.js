(function () {
  // Date picker: jump to the chosen edition.
  var sel = document.getElementById('datesel');
  if (sel) sel.addEventListener('change', function () { location.href = sel.value; });

  // MCQs: tap an option to see if it is right and read the explanation. Nothing is stored.
  document.querySelectorAll('.mcq').forEach(function (box) {
    var answer = box.getAttribute('data-answer');
    box.querySelectorAll('button').forEach(function (b) {
      b.addEventListener('click', function () {
        if (box.getAttribute('data-done')) return;
        box.setAttribute('data-done', '1');
        var pick = b.getAttribute('data-opt');
        box.querySelectorAll('button').forEach(function (x) {
          if (x.getAttribute('data-opt') === answer) x.classList.add('right');
        });
        if (pick !== answer) b.classList.add('wrong');
        var why = box.querySelector('.why');
        if (why) why.hidden = false;
      });
    });
  });

  // Archive: filter by exam.
  var chips = document.querySelectorAll('.chips.filter button');
  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      chips.forEach(function (x) { x.classList.remove('on'); });
      c.classList.add('on');
      var want = c.getAttribute('data-exam');
      document.querySelectorAll('.list li').forEach(function (li) {
        var has = (li.getAttribute('data-exams') || '').split(',').indexOf(want) >= 0;
        li.style.display = (!want || has) ? '' : 'none';
      });
    });
  });
})();
