import instaloader
import time
import os

if __name__ == "__main__":
    user = os.environ["USER"]
    pw = os.environ["PASSWORD"]

    loader = instaloader.Instaloader(
        # storyitem_metadata_txt_pattern="logs.txt"
    )

    # Login (optional)
    # If you want to download stories from private profiles, you need to login with your Instagram credentials.
    loader.login(user=user, passwd=pw)
    #
    # Define the profile name
    profile_name = ""  # Replace "username" with the actual username of the profile you want to download stories from

    # loader.download_profile(profile_name, download_stories_only=True,profile_pic=False)

    # Retrieve the profile metadata
    profile = instaloader.Profile.from_username(loader.context, profile_name)

    stories = loader.get_stories(userids=[profile.userid])

    for story in stories:

        for item in story.get_items():
            local_timestamp = item.date_local
            date = local_timestamp.strftime('%Y-%m-%d')
            loader.dirname_pattern = f"data/{date}/"  # f'highlights/{item.owner_username}'
            # loader.filename_pattern = f'{item.title}'
            loader.download_storyitem(item, target='')


    # Download stories
    # loader.download_stories(userids=[profile.userid], filename_target="{date_utc}_story")

    print("Stories downloaded successfully.")