# DiscordPlaysPokemonYellow
![image](https://user-images.githubusercontent.com/1060681/142716401-301aeb86-1d1f-46ff-8478-316fd2485925.png)

[Invite The Bot To Your Server!](https://discord.com/api/oauth2/authorize?client_id=904473712655487056&scope=applications.commands)

## What is this?
Yeah it's another X plays Pokemon, I know. I wanted to have one for a Discord server I'm in though and could only find self hosted bots and not one where people could just invite.
There was one that I could just invite, but all Discord servers shared the same instance of Pokemon.

So, I wanted to try serverless with AWS Lambda and allowing each server to have their own instance of the game. Everytime an action is performed, the previous game state is fetched from DynamoDB using the Discord server as the key, [PyBoy](https://github.com/Baekalfen/PyBoy) then loads the game state, processes the input, and advances the game 300 frames, then saves the game state back into DynamoDB.

## Why?
Well I wanted to try writing something with a serverless function. This means that if nobody uses my bot, then it costs me nothing to host! If people do use my bot, it'll scale well.

## How do I use it?
Invite the bot to your server, and if you're a manager of the server go to a channel and type /pokemonplay to start

## I'm trying to host this myself and it's not working
In your AWS function add an aditional layer with a GameBoy pokemon rom named yellow.gbc
