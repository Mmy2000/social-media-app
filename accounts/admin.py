from django.contrib import admin
from .models import User, UserProfile, FriendshipRequest
from django.contrib.auth.admin import UserAdmin



class AccountAdmin(UserAdmin):
    # Display fields in the admin list view
    list_display = ('email', 'first_name', 'last_name', 'username','source' ,'last_login', 'date_joined', 'is_active', 'is_admin')
    
    # Fields that can be clicked to open the user’s detail view
    list_display_links = ('email', 'first_name', 'last_name')
    
    # Make certain fields read-only
    readonly_fields = ('last_login', 'date_joined', 'otp')
    
    # Add filters for user status and dates
    list_filter = ('is_active', 'is_admin', 'date_joined')
    
    # Add a search bar for key fields
    search_fields = ('email', 'username', 'first_name', 'last_name','source')
    
    # Customize the form fieldsets to organize fields better
    fieldsets = (
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'username')}),
        ('Permissions', {'fields': ('is_admin', 'is_staff', 'is_active', 'is_superadmin')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
        ('Password', {'fields': ('password',)}),
    )
    

    ordering = ('-date_joined',)

    # To avoid errors with permissions
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

admin.site.register(User, AccountAdmin)
admin.site.register(UserProfile)
admin.site.register(FriendshipRequest)