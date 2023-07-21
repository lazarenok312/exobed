from django.views.generic import DetailView

from account.models import Profile


class ProfileDetailView(DetailView):
    model = Profile
    template_name = 'profile/profile_detail.html'
    context_object_name = 'profile'
    slug_field = 'slug'
