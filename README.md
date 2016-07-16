# Tornado + Flask + VueJS

Dummy stupid example...

Launch the server:
```
python tornadosse.py
```

Go to: `http://localhost:8000/`

Type 1, 2 or 3 in the form.

The routing:
```python

[
    (r'/', MainHandler), # Reroutes to /static/index.html
    (r'/events', EventSource, dict(source=publisher)), # SSE
    (r'/static/(.*)', web.StaticFileHandler, {'path': "./static"}),
    (r".*", web.FallbackHandler, dict(fallback=flask_handler)), # REST Calls handled by FLASK
],
```

Vue.js code: `/static/index.html`
