from os import mkdir
from os.path import isdir, abspath
from sqlite3 import connect as sqlite_connect
from sqlite3 import Row as sqlite_row
from json import dumps as json_dumps

from bottle import get, post, delete, route, run, static_file, HTTPResponse, response, request

STATIC_ROOT = abspath("bower_components")

HOME = open("home.html", "r").read()

SCHEMA = """
	create table Diagram (
		name text primary key,
		content text not null
	);
"""


def db_integrity_check(conn):
	c = conn.cursor()
	c.execute("select sql from sqlite_master where type='table' "
		"and name in ('Diagram')")
	return len(c.fetchall()) == 1


conn = sqlite_connect("diagrams.db", check_same_thread=False)
conn.row_factory = sqlite_row

if not db_integrity_check(conn):
	print("Integrity check failed... Recreating database.")
	conn.cursor().executescript(SCHEMA)
	conn.commit()


@get("/diagrams")
def get_diagrams():
	diagrams = {}

	response.content_type = "application/json"

	c = conn.cursor()
	c.execute("select name, content from Diagram")

	for row in c.fetchall():
		diagrams[row["name"]] = row["content"]

	return json_dumps(diagrams)


@delete("/diagram/<name>")
def delete_diagram(name):
	successful = True

	c = conn.cursor()
	c.execute("select name from Diagram where name = ?", (name, ))

	if len(c.fetchall()) == 0:
		successful = False
	else:
		c.execute("delete from Diagram where name = ?", (name, ))
	
	conn.commit()


@post("/diagram/<name>")
def post_diagram(name):
	content = request.forms.get("content")

	c = conn.cursor()
	c.execute("select name from Diagram where name = ?", (name, ))

	if len(c.fetchall()) == 0:
		c.execute("insert into Diagram values (?, ?)", (name, content))
	else:
		c.execute("update Diagram set content = ? where name = ?", 
			(content, name))
	conn.commit()


@get("/diagram/<name>")
def get_diagram(name):
	c = conn.cursor()
	c.execute("select content from Diagram where name = ?", (name))

	result = c.fetchall()

	if len(result) == 0:
		return HTTPResponse(status=404)
	else:
		return result[0]


@get("/static/<filepath:path>")
def server_static(filepath):
	return static_file(filepath, root=STATIC_ROOT)

@get("/")
def home():
	return HOME

run(host="localhost", port=8080, debug=True)