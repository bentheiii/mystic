# Mystic
Mystic is a collection of programs and libraries to make it easier to store secret key-value pairs (most commonly, passwords).

**WARNING** while this project is in beta, it is recommended that you keep a backup of your secret data aside from this project.

## Introduction
The project centers around encrypted files called mystics. A mystic contains many key-value pairs and can be encrypted with multiple master passwords. That means that you can have two or more master passwords to unlock all your keys.

## Parts
* **mysticlib:** a python library for interacting with mystic files.
* **mysticCLI:** a python command line interface tool for creating and manipulating mystics.
* **mysticweb:** a flask web app for reading mystics remotely, without having to install any additional programs beyond a web browser.

## Installing the CLI
* install [python](https://www.python.org/), make sure it at least version 3.6 and to install pip as well.
* download this repository.
* install the required packages:
  * either manually install cryptography>=2.2 and optionally pyperclip>=1.6
  * OR run setup-cli-environment.bat from the repository
* run mysticCLI.bat to check that everything works

## Getting things running
### Create a mystic
* run mysticCLI.bat
* enter * and press enter to work on a new file
* enter "add_password" to add master passwords to the new mystic
  * you can add additional master passwords as you want.
* enter "add" to insert new key-value pairs to the mystic
  * you can instead use C syntax "add('key','value')"
  * you can also insert from a csv-like file with "load"
  * at any point, you can see all the key-value pairs with "dump"
  * you can learn about all the functions with "help"
* enter "save" and the filename to save the mystic to a file (use the extension .scm)
* enter "quit" to exit the CLI
### Open a mystic with the CLI
* run mysticCLI.bat
* enter the name of the mystic file to open it
* use "dump", "get", "search", or "lookup" to look up values in the mystic
  * you can use "help" and a command name to get help on that command
* if you make any changes, don't forget to save
* enter "quit" to exit the CLI
### Open a mystic with the web app
* enter the [web app](https://mysticweb.herokuapp.com/)
* click on "Choose File" and choose the mystic you want
* enter your password in the "enter password"
* click "submit"
* in the resulting window you can see all your keys
  * by clicking on a key, it's value will be displayed in a black box below
  * you can filter the keys with the textbox
## Security
### The mystic
**WARNING** No encryption is better than the key used to encrypt it. Mystic does not enforce any kind of restrictions on the key you can use, but use common sense when picking your password.

The mystic itself is encrypted with [fernet encryption](https://asecuritysite.com/encryption/fer), a wrapper of [AES](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard). It also uses [SHA256](https://en.wikipedia.org/wiki/SHA-2) to ensure the mystic has not been modified. A secure key is derived from the master password using [PBKDF2](https://en.wikipedia.org/wiki/PBKDF2) with 100,000 iterations (this number can be changed using mysticlib, but the default is 100,000).

The master key is encrypted once for each master password, there is no indication which of the master passwords is encrypted where.
### The CLI
Since the cli is run on the machine, there is little threat from attackers, unless spyware is installed on the machine (but by then there is nothing to be done).
### The web app
The web app warns when it is being used insecurely. When used securely, all traffic is authenticated and encrypted.

Still, sending such sensitive data over the web may be undesirable in any state, so it is recommended that you use the CLI whenever possible. Using the pre-load filter on the web app is also slightly more secure than not using it.

---------------
In any case, both the CLI and the app will automatically exit after 30 minutes, to prevent prying eyes.