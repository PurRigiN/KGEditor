import logging
from . import api
from flask import jsonify, g, request, session
from kgeditor.utils.common import login_required
from kgeditor import db, arango_conn
from kgeditor.models import Domain
from kgeditor.utils.response_code import RET
from sqlalchemy.exc import IntegrityError
from pyArango.theExceptions import CreationError

@api.route('/domain', methods=['POST'])
@login_required
def add_domain():
    """添加领域

    Add some data in this routing

    Args:
        name: 

    Returns:
        pass
    """
    # get request json, return dict
    user_id = g.user_id
    req_dict = request.get_json()
    name = req_dict.get('name')
    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    try:
        domain = Domain.query.filter_by(name=name).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    else:
        if domain is not None:
            return jsonify(errno=RET.DATAEXIST, errmsg='"{}"领域已存在'.format(name))
    # 5.save graph info to db
    domain = Domain(name=name, creator_id=user_id)
    try:
        db.session.add(domain)
        db.session.commit()
        arango_conn.createDatabase(name="domain_{}".format(domain.id))
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='添加领域失败')
        # 6. use neo4j create graph
    
    return jsonify(errno=RET.OK, errmsg="新建领域成功")

@api.route('/domain', methods=['GET'])
@login_required
def list_domain():
    # pass
    # get request json, return dict
    try:
        domain_list = Domain.query.all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    domain_dict_list = []
    for domain in domain_list:
        domain_dict_list.append(domain.to_dict())
    
    return jsonify(errno=RET.OK, errmsg="OK", data=domain_dict_list)

@api.route('/domain/<domain_id>', methods=['DELETE'])
@login_required
def delete_domain(domain_id):
    # pass
    user_id = g.user_id
    req_dict = request.get_json()
    if not domain_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    try:
        domain = Domain.query.filter_by(id=domain_id, creator_id=user_id).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    else:
        if domain is None:
            return jsonify(errno=RET.DATAEXIST, errmsg='领域不存在')
    # 5.save graph info to db
    try:
        db.session.delete(domain)
        db.session.commit()
        url = f'{arango_conn.getURL()}/database/domain_{domain.id}'
        arango_conn.session.delete(url)
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='删除领域失败')     
    return jsonify(errno=RET.OK, errmsg="删除领域成功")

@api.route('/domain/<domain_id>', methods=['PATCH'])
@login_required
def rename_domain(domain_id):
    req_dict = request.get_json()
    name = req_dict.get('name')
    if not all([domain_id, name]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        domain = Domain.query.filter_by(id=domain_id).first()
        domain.name = name
        db.session.commit()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    return jsonify(errno=RET.OK, errmsg="修改成功")