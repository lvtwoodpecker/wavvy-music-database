#!/usr/bin/env python3
"""Setup system user for public playlists like 'Now Trending'."""

from app.db.sqlalchemy_engine import SessionLocal
from app.models.User import User, UserRole
from app.models.Listener import Listener
from app.models.Playlist import Playlist
from sqlalchemy import select
import uuid

def setup_system_user():
    with SessionLocal() as db:
        # Check if system user already exists
        system_user = db.scalars(
            select(User).where(User.email == 'system@wavvy.local')
        ).first()
        
        if system_user:
            print("System user already exists")
            return system_user.user_id
        
        # Create system user
        system_user = User(
            email='system@wavvy.local',
            username='system',
            first_name='Wavvy',
            last_name='System',
            password_hash='disabled',  # System account, no password
            country='US',
            role=UserRole.listener,
            status='active'
        )
        db.add(system_user)
        db.flush()
        
        # Create system listener
        system_listener = Listener(
            listener_id=uuid.uuid4(),
            user_id=system_user.user_id,
            ad_free=True
        )
        db.add(system_listener)
        db.commit()
        
        print(f"✓ Created system user (ID: {system_user.user_id})")
        print(f"✓ Created system listener (ID: {system_listener.listener_id})")
        
        # Update "Now Trending" playlist
        now_trending = db.scalars(
            select(Playlist).where(Playlist.id == 9)
        ).first()
        
        if now_trending:
            now_trending.owner_id = system_listener.listener_id
            now_trending.is_public = True
            now_trending.is_collaborative = False
            db.commit()
            print(f"✓ Updated 'Now Trending' playlist to be public and owned by system user")
        else:
            print("⚠ 'Now Trending' playlist (ID 9) not found")
        
        return system_user.user_id

if __name__ == '__main__':
    setup_system_user()
