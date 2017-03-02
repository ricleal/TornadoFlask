import logging

from flask import Flask, jsonify

from faker import Factory

"""
Dummy REST server called by tornado
"""

fake = Factory.create()
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

def task_maker(i):
    fake.seed(i)
    return {
        'id' : i,
        'title' : fake.catch_phrase(),
        'description': fake.text(),
        'done': False,
    }

app = Flask(__name__)

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = task_maker(task_id)
    return jsonify({'task': task})
