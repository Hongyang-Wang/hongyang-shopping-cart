Main Ideas:

	- Create an unique id for each book
	- Create a cart Entity for each user (including the temporary user) in the database with user name as the key
	- If the user has not logged in, assign him a cookie_id as his user name (also as the key for his temporary cart)
	- The cart entity only stores the id and genre for the book
	- When display the cart, the program will search the book information according to the id and genre
	- Only after a user has logged in can he checkout
	- When a user log in, merge the temporary cart with his cart and delete the temporary cart from the database
	- After checking out, remove all the books in his cart
	