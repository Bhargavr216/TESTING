const textEl = document.getElementById('text')
const speedEl = document.getElementById('speed')
const text = 'Itachi Uchiha (うちは イタチ, Uchiha Itachi) is a character in the Naruto manga and anime series created by Masashi Kishimoto. Itachi is the older brother of Sasuke Uchiha, and is responsible for killing all the members of their clan, sparing only Sasuke. He appears working as a terrorist from the organisation Akatsuki and serves as Sasukes greatest enemy.During the second part of the manga, Itachi becomes involved in attacks to ninjas possessing tailed-beast creatures (Jinchuriki) until facing Sasuke in a one-on-one battle. Although Itachi perishes during the final duel, it is later revealed that Itachi had a secret reason for assassinating the Uchiha clan. Itachi is a playable character in most of the video games from the series. Itachis character has been popular with readers of the manga[6] and has been positively received by critics. He is considered by many to be one of the best characters in the series. His appearance as an antagonist has been praised by several writers, although some have considered his initial appearance to be unsurprising. The gradual revelations of his past and its impact on the story has also received positive reception,[7][8] and his fights were noted to be one of the best in the series.[9][10][11] Numerous types of merchandise have been released in Itachis likeness, including keychains, plush dolls and figurines.     '
let idx = 1
let speed = 300 / speedEl.value

writeText()

function writeText() {
    textEl.innerText = text.slice(0, idx)

    idx++

    if(idx > text.length) {
        idx = 1
    }

    setTimeout(writeText, speed)
}


speedEl.addEventListener('input', (e) => speed = 300 / e.target.value)