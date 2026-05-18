"use strict";

window.addEventListener('load', app);

let gameBoard = ['', '', '', '', '', '', '', '', '']; 
let turn = 0; 
let winner = false;

const player = (name) => {
  name = name;
  return {name};
 };

 let playerX = player("");
 let playerY = player("");

function app() {
  let inputField = document.querySelector('.input-field').focus();

  const addPlayerForm = document.getElementById('player-form');
  addPlayerForm.addEventListener('submit', addPlayers);

  let replayButton = document.querySelector('.replay-btn');
  replayButton.addEventListener('click', resetBoard);
}

function addPlayers(event) {
  event.preventDefault();

  if (this.player1.value === '' || this.player2.value === '') {
    alert('You Must Enter a Name for Each Field');
    return;
  }

  const playerFormContainer = document.querySelector('.enter-players');
  const boardMain = document.querySelector('.board__main');
  playerFormContainer.classList.add('hide-container');
  boardMain.classList.remove('hide-container');

  playerX.name = this.player1.value;
  playerY.name = this.player2.value;
  buildBoard();
}

function currentPlayer() {
  return turn % 2 === 0 ? 'X' : 'O';
}

window.addEventListener("resize", onResize);
function onResize() {
  let allCells = document.querySelectorAll('.board__cell');
  let cellHeight = allCells[0].offsetWidth;
  
  allCells.forEach( cell => {
    cell.style.height = `${cellHeight}px`;
  });
}

function buildBoard() {
  let resetContainer = document.querySelector('.reset');
  resetContainer.classList.remove('reset--hidden');

  onResize();
  addCellClickListener();
  changeBoardHeaderNames();
}

function makeMove(event) {
  console.log(turn);
  
  let currentCell = parseInt(event.currentTarget.firstElementChild.dataset.id);
  let cellToAddToken = document.querySelector(`[data-id='${currentCell}']`);
  
  if (cellToAddToken.innerHTML !== '') {
    console.log('This cell is already taken.');
    return;
  } else {
    if (currentPlayer() === 'X') {
      cellToAddToken.textContent = currentPlayer();
      gameBoard[currentCell] = 'X';
    } else {
      cellToAddToken.textContent = currentPlayer();
      gameBoard[currentCell] = 'O';
    }
  }
    
  isWinner();
    
  turn ++;

  changeBoardHeaderNames();
}

function checkIfTie() {
  if (turn > 7) {
    alert('game over a tie')
  }
}

function isWinner() {
  const winningSequences = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
  ];

  winningSequences.forEach( winningCombos => {
    let cell1 = winningCombos[0];
    let cell2 = winningCombos[1];
    let cell3 = winningCombos[2];
    if (
      gameBoard[cell1] === currentPlayer() &&
      gameBoard[cell2] === currentPlayer() &&
      gameBoard[cell3] === currentPlayer()
    ) {

      
      const cells = document.querySelectorAll('.board__cell');
      let letterId1 = document.querySelector(`[data-id='${cell1}']`);
      let letterId2 = document.querySelector(`[data-id='${cell2}']`);
      let letterId3 = document.querySelector(`[data-id='${cell3}']`);
      
      cells.forEach( cell => {
        let cellId = cell.firstElementChild.dataset.id;	

        if (cellId == cell1 || cellId == cell2 || cellId == cell3 ) {
          cell.classList.add('board__cell--winner');
        }
      });

      let currentPlayerText = document.querySelector('.board___player-turn');
      if (currentPlayer() === 'X') {
        currentPlayerText.innerHTML = `
          <div class="congratulations">Congratulations ${playerX.name}</div>
          <div class="u-r-winner">You are our winner!</div>
        `;
        winner = true;
        removeCellClickListener();
        return true;
      } else {
        currentPlayerText.innerHTML = `
          <div class="congratulations">Congratulations ${playerY.name}</div>
          <div class="u-r-winner">You are our winner!</div>
        `;
        winner = true;
        removeCellClickListener();
        return true;
      }
    }
  });

  if (!winner) {
    checkIfTie();
  }
  
  return false;
}

function changeBoardHeaderNames() {
  if (!winner) {
    let currentPlayerText = document.querySelector('.board___player-turn');
    if (currentPlayer() === 'X') {
      currentPlayerText.innerHTML = `
        <span class="name--style">${playerX.name}</span>, you are up!
        <div class="u-r-winner"></div>
      `
    }  else {
      currentPlayerText.innerHTML = `
        <span class="name--style">${playerY.name}</span>, you are up.
        <div class="u-r-winner"></div>
      `
    }
  }
}

function resetBoard() {
  console.log('resetting');
  
  gameBoard = ['', '', '', '', '', '', '', '', '']; 
  
  let cellToAddToken = document.querySelectorAll('.letter');
  cellToAddToken.forEach( square => {
    square.textContent = '';
    square.parentElement.classList.remove('board__cell--winner');
  });

  turn = 0;
  winner = false;

  let currentPlayerText = document.querySelector('.board___player-turn');
  currentPlayerText.innerHTML = `
    <span class="name--style">${playerX.name}</span>, you are up!
    <div class="u-r-winner"></div>
  `

  addCellClickListener();
}

function addCellClickListener() {
  const cells = document.querySelectorAll('.board__cell');
  cells.forEach( cell => {
    cell.addEventListener('click', makeMove);
  });
}

function removeCellClickListener() {
  let allCells = document.querySelectorAll('.board__cell');
  allCells.forEach( cell => {
    cell.removeEventListener('click', makeMove);
  });
}

