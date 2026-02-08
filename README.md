# EDUCATIONAL LUDO 

---

**Educational Ludo** is a multiplayer board game for kids or adults that combines the classic Ludo gameplay with fun educational questions.  
Players compete to reach the finish first while answering quiz questions that test their knowledge and add an extra challenge to every move.
Play with up to 4 friends per game, whether you choose the macedonian or english version it's all up to you! 

The game is designed for:
- Playing with friends 
- Learning through interactive multiple-choice and true/false questions
- Enjoying a colorful and simple user interface built with Python and Pygame

What separates it from a classic Ludo is:
- While playing you can click on the QUIZ button that will prompt you to click on a number between 1-6 which will then (let's say u selected 4) if answering correctly move u up 4 tiles but if selecting wrong your pawn will be moved 4 tiles backwards
- If u and a opponent both are on a tile - a DUEL occurs, you and your opponent answer questions as fast and as correctly as you can. The person with the most correctly answered questions in the short amount of time gives WINS the duel and stays on the tile, the losing pawn returns to it's home base 

---

The game can also be downloaded and played with friends as a standalone **.exe** file.

**You can preview the user interface and gameplay inside the demo folder [here](https://github.com/marijanamarijana/educational_ludo/tree/main/demo).**

---

To start the multiplayer ludo game *LOCALY* on your machine in console / terminal, run the following commands:
1. **python server_tcp.py**
2. **python client_tcp.py** (run it in 2 separate terminals for 2 players - you should have somthing like on the picture -
   for 3 players you should have 3 consoles with **python client_tcp.py** and one with  **python server_tcp.py**)
<img width="553" height="101" alt="image" src="https://github.com/user-attachments/assets/85cf5b82-e3fe-44cb-a256-319a156a50ba" />

----

To start the multiplayer ludo ON THE CLOUD (on a hosted server) on your machine in the client_tcp.py file uncomment the settings for 
the host and start it with the command **python client_tcp.py**. You can also start as many clients as u like here - starting the client is the same as it is localy and the server is already provided for you.

