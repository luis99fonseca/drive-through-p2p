
gnome-terminal --title="Rececionista" --geometry 60x25+1250+0 -e "python3 Receptionist.py" &
gnome-terminal --title="Empregado" --geometry 60x25+1250+1000 -e "python3 Employee.py" &
gnome-terminal --title="Restaurant" --geometry 60x25+0+0 -e "python3 Restaurant.py" & 
sleep 3
gnome-terminal --title="Cozinheiro" --geometry 60x25+0+1000 -e "python3 Chef.py "&
sleep 5
# gnome-terminal --title="Cliente" --geometry 60x25+0+1000 -e "python3 client.py "
for i in {1..2} 
do
	port=$((5010+$i))
	gnome-terminal --title="Cliente $i" -e "python3 client.py -p $port" &
done