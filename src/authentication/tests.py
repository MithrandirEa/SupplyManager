from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, AnonymousUser
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import HttpResponse

from .models import User
from .decorators import role_required

class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'password': 'testpassword123',
            'role': User.CREW
        }

    def test_create_standard_user(self):
        """Test creating a standard user with default role."""
        user = get_user_model().objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpassword123'))
        self.assertEqual(user.role, User.CREW)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin_user = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'password123')
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_active)
        # superuser created via create_superuser doesn't necessarily have role=ADMIN unless customized manager
        # But we can verify it's a superuser.
        
    def test_string_representation(self):
        """Test the string representation of the user."""
        user = get_user_model().objects.create_user(**self.user_data)
        expected_str = f'{user.username} - {user.get_role_display()}'
        self.assertEqual(str(user), expected_str)

    def test_role_assignment_and_groups(self):
        """Test that assigning a role adds the user to the correct group."""
        # Test CREW
        crew_user = get_user_model().objects.create_user(username='crew', password='password', role=User.CREW)
        self.assertTrue(crew_user.groups.filter(name='Équipe').exists())
        
        # Test DIRECTOR
        director_user = get_user_model().objects.create_user(username='director', password='password', role=User.DIRECTOR)
        self.assertTrue(director_user.groups.filter(name='Responsable').exists())
        
        # Test ADMIN
        admin_user = get_user_model().objects.create_user(username='admin', password='password', role=User.ADMIN)
        self.assertTrue(admin_user.groups.filter(name='Admin').exists())

    def test_role_change_updates_group(self):
        """Test that changing a role updates the group."""
        user = get_user_model().objects.create_user(username='changer', password='password', role=User.CREW)
        self.assertTrue(user.groups.filter(name='Équipe').exists())
        
        user.role = User.DIRECTOR
        user.save()
        
        self.assertFalse(user.groups.filter(name='Équipe').exists())
        self.assertTrue(user.groups.filter(name='Responsable').exists())


class UsernameValidatorTest(TestCase):
    def test_username_with_spaces_valid(self):
        """Test that username with spaces is allowed."""
        user = User(username="User Name With Spaces", password="password")
        try:
            user.full_clean()
        except ValidationError as e:
            self.fail(f"Username with spaces failed validation: {e}")

    def test_username_with_special_chars_valid(self):
        """Test that username with @/./+/-/_ is allowed."""
        user = User(username="user.name@domain+test_1", password="password")
        try:
            user.full_clean()
        except ValidationError:
            self.fail("Username with allowed special chars failed validation")

    def test_username_invalid_chars(self):
        """Test that username with invalid characters raises ValidationError."""
        user = User(username="User#Name", password="password") # # is not allowed
        with self.assertRaises(ValidationError):
            user.full_clean()


class RolePermissionTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # We need to save users to DB because ManyToMany relations (groups) require it, 
        # and role_required might check attributes that depend on DB state if modified, 
        # though strictly role is a field. 
        # More importantly, create_user ensures password hashing.
        self.crew_user = User.objects.create_user(username='crew', password='password', role=User.CREW)
        self.director_user = User.objects.create_user(username='director', password='password', role=User.DIRECTOR)
        self.admin_user = User.objects.create_user(username='admin', password='password', role=User.ADMIN)

    def test_role_required_decorator_access(self):
        """Test that role_required decorator allows correct roles."""
        
        @role_required([User.ADMIN, User.DIRECTOR])
        def protected_view(request):
            return HttpResponse("Access Granted")

        # Test DIRECTOR access (should be allowed)
        request = self.factory.get('/protected/')
        request.user = self.director_user
        response = protected_view(request)
        self.assertEqual(response.status_code, 200)

        # Test ADMIN access (should be allowed)
        request = self.factory.get('/protected/')
        request.user = self.admin_user
        response = protected_view(request)
        self.assertEqual(response.status_code, 200)

    def test_role_required_decorator_denial(self):
        """Test that role_required decorator denies incorrect roles."""
        
        @role_required([User.ADMIN, User.DIRECTOR])
        def protected_view(request):
            return HttpResponse("Access Granted")

        # Test CREW access (should be denied)
        request = self.factory.get('/protected/')
        request.user = self.crew_user
        
        with self.assertRaises(PermissionDenied):
            protected_view(request)

    def test_role_required_decorator_login_required(self):
        """Test that role_required enforces login."""
        
        @role_required([User.ADMIN])
        def protected_view(request):
            return HttpResponse("Access Granted")

        request = self.factory.get('/protected/')
        request.user = AnonymousUser()
        
        # @login_required usually redirects to LOGIN_URL (302)
        response = protected_view(request)
        self.assertEqual(response.status_code, 302)
