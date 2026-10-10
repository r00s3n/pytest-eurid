#!/bin/sh
# Encode a password as base64 for the *_PWD fields in .env files.
# The password is read without echo, so it does not end up in your shell history.

printf "Password: "
stty -echo
read -r password
stty echo
printf "\n"

printf '%s' "$password" | base64 -w 0
printf "\n"
