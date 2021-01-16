"""
entity and relation types are defined as collection in ArangoDB,
and all operations of them are assigned in this file
"""
from . import api
from flask import jsonify, g, request, session
from kgeditor.utils.common import login_required, verify_graph
from kgeditor import db, arango_conn
from kgeditor.models import Graph
from kgeditor.utils.response_code import RET
from kgeditor.utils.type_dict import type_dict
from sqlalchemy.exc import IntegrityError
import logging
from pyArango.consts import *
from pyArango.theExceptions import CreationError
@api.route('list_documents', methods=['POST'])
@login_required
@verify_graph
def list_documents():
    req_dict = request.get_json()
    documents = []
    graph_db = arango_conn['graph_{}'.format(g.graph_id)]
    types = type_dict.get(req_dict.get('type'))
    if types is None:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不正确") 
    for name, collection in graph_db.collections.items():
        if collection.type == types and not name.startswith('_'):
            documents.append(name)
    return jsonify(errno=RET.OK, errmsg="OK", data=documents)

@api.route('add_document', methods=['POST'])
@login_required
@verify_graph
def add_document():
    documents = []
    graph_db = arango_conn['graph_{}'.format(g.graph_id)]
    req_dict = request.get_json()
    properties = req_dict.get('properties')
    types = req_dict.get('type')
    if properties is None:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    if not isinstance(properties, dict):
        return jsonify(errno=RET.PARAMERR, errmsg='参数类型错误')
    if 'name' not in properties or 'type' is None:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    try:
        msg = graph_db.createCollection(className=types, **properties)    
    except CreationError as e:
        logging.info(e)
        return jsonify(error=RET.DATAEXIST, errmsg="Collection已存在")
    else:
        return jsonify(errno=RET.OK, errmsg="创建Collection成功")