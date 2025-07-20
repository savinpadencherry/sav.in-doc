"""
Authentication Routes - Complete implementation
"""

from flask import Blueprint, request, jsonify, session # type: ignore
from app.services.auth_service import AuthService
from app.models.user import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration (bypassed for demo)"""
    try:
        data = request.get_json()
        
        # In demo mode, always return success
        user = AuthService.get_current_user()
        
        return jsonify({
            'success': True,
            'message': 'Registration bypassed in demo mode',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login (bypassed for demo)"""
    try:
        data = request.get_json()
        
        # In demo mode, always return success
        user = AuthService.get_current_user()
        user.update_last_login()
        
        # Set session
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'success': True,
            'message': 'Login bypassed in demo mode',
            'user': user.to_dict(include_stats=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Login failed: {str(e)}'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout"""
    try:
        # Clear session
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Logout failed: {str(e)}'
        }), 500

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    try:
        user = AuthService.get_current_user()
        
        return jsonify({
            'success': True,
            'user': user.to_dict(include_stats=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get user info: {str(e)}'
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update user profile (demo mode)"""
    try:
        data = request.get_json()
        user = AuthService.get_current_user()
        
        # Update basic profile info
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Profile update failed: {str(e)}'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password (disabled in demo)"""
    return jsonify({
        'success': False,
        'message': 'Password change disabled in demo mode'
    }), 400
