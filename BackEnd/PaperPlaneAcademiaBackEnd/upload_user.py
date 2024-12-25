from users.models import User
from papers.models import Paper
from comments.models import Comment
from information.models import Information

# 创建论文样例数据
paper1 = Paper.objects.create(
    title='Paper Title 1',
    authors=['Author 1', 'Author 2'],
    institutions=['Institution 1', 'Institution 2'],
    publish_date='2023-01-01',
    journal='Journal 1',
    volume='1',
    issue='1',
    keywords=['Keyword1', 'Keyword2'],
    citation_count=10,
    download_link='http://example.com/download1',
    original_link='http://example.com/original1',
    references_works=['Reference 1', 'Reference 2'],
    research_fields=['Field 1', 'Field 2'],
    status='Published',
    created_time='2023-01-01 00:00:00',
    remarks='Remarks for Paper 1'
)

paper2 = Paper.objects.create(
    title='Paper Title 2',
    authors=['Author 3', 'Author 4'],
    institutions=['Institution 3', 'Institution 4'],
    publish_date='2023-02-01',
    journal='Journal 2',
    volume='2',
    issue='2',
    keywords=['Keyword3', 'Keyword4'],
    citation_count=20,
    download_link='http://example.com/download2',
    original_link='http://example.com/original2',
    references_works=['Reference 3', 'Reference 4'],
    research_fields=['Field 3', 'Field 4'],
    status='Published',
    created_time='2023-02-01 00:00:00',
    remarks='Remarks for Paper 2'
)

paper3 = Paper.objects.create(
    title='Paper Title 3',
    authors=['Author 5', 'Author 6'],
    institutions=['Institution 5', 'Institution 6'],
    publish_date='2023-03-01',
    journal='Journal 3',
    volume='3',
    issue='3',
    keywords=['Keyword5', 'Keyword6'],
    citation_count=30,
    download_link='http://example.com/download3',
    original_link='http://example.com/original3',
    references_works=['Reference 5', 'Reference 6'],
    research_fields=['Field 5', 'Field 6'],
    status='Published',
    created_time='2023-03-01 00:00:00',
    remarks='Remarks for Paper 3'
)

paper4 = Paper.objects.create(
    title='Paper Title 4',
    authors=['Author 7', 'Author 8'],
    institutions=['Institution 7', 'Institution 8'],
    publish_date='2023-04-01',
    journal='Journal 4',
    volume='4',
    issue='4',
    keywords=['Keyword7', 'Keyword8'],
    citation_count=40,
    download_link='http://example.com/download4',
    original_link='http://example.com/original4',
    references_works=['Reference 7', 'Reference 8'],
    research_fields=['Field 7', 'Field 8'],
    status='Published',
    created_time='2023-04-01 00:00:00',
    remarks='Remarks for Paper 4'
)

paper5 = Paper.objects.create(
    title='Paper Title 5',
    authors=['Author 9', 'Author 10'],
    institutions=['Institution 9', 'Institution 10'],
    publish_date='2023-05-01',
    journal='Journal 5',
    volume='5',
    issue='5',
    keywords=['Keyword9', 'Keyword10'],
    citation_count=50,
    download_link='http://example.com/download5',
    original_link='http://example.com/original5',
    references_works=['Reference 9', 'Reference 10'],
    research_fields=['Field 9', 'Field 10'],
    status='Published',
    created_time='2023-05-01 00:00:00',
    remarks='Remarks for Paper 5'
)

# 创建用户样例数据
def create_user(username, password, email, institution, user_type, bio, research_fields, avatar, published_papers_count, register_time, status, uploaded_papers, favorite_papers, recent_viewed_papers, inbox, remarks):
    if not User.objects.filter(username=username).exists():
        user = User.objects.create(
            username=username,
            password=password,
            email=email,
            institution=institution,
            user_type=user_type,
            bio=bio,
            research_fields=research_fields,
            avatar=avatar,
            published_papers_count=published_papers_count,
            register_time=register_time,
            status=status,
            inbox=inbox,
            remarks=remarks
        )
        user.uploaded_papers.add(*uploaded_papers)
        user.favorite_papers.add(*favorite_papers)
        user.recent_viewed_papers.add(*recent_viewed_papers)
        return user
    else:
        print(f"User with username '{username}' already exists.")
        return None

user1 = create_user(
    username='user1',
    password='password1',
    email='user1@example.com',
    institution='Institution 1',
    user_type='researcher',
    bio='Bio of user1',
    research_fields={'field1': 'AI', 'field2': 'ML'},
    avatar='avatar1.png',
    published_papers_count=5,
    register_time='2023-01-01 00:00:00',
    status='active',
    uploaded_papers=[paper1],
    favorite_papers=[paper2],
    recent_viewed_papers=[paper1, paper2],
    inbox={'messages': []},
    remarks='Remarks for user1'
)

user2 = create_user(
    username='user2',
    password='password2',
    email='user2@example.com',
    institution='Institution 2',
    user_type='reviewer',
    bio='Bio of user2',
    research_fields={'field1': 'Data Science', 'field2': 'Big Data'},
    avatar='avatar2.png',
    published_papers_count=3,
    register_time='2023-02-01 00:00:00',
    status='active',
    uploaded_papers=[paper2],
    favorite_papers=[paper1],
    recent_viewed_papers=[paper1, paper2],
    inbox={'messages': []},
    remarks='Remarks for user2'
)

user3 = create_user(
    username='user3',
    password='password3',
    email='user3@example.com',
    institution='Institution 3',
    user_type='normalUser',
    bio='Bio of user3',
    research_fields={'field1': 'Physics', 'field2': 'Quantum Mechanics'},
    avatar='avatar3.png',
    published_papers_count=2,
    register_time='2023-03-01 00:00:00',
    status='active',
    uploaded_papers=[paper1],
    favorite_papers=[paper2],
    recent_viewed_papers=[paper1, paper2],
    inbox={'messages': []},
    remarks='Remarks for user3'
)

user4 = create_user(
    username='user4',
    password='password4',
    email='user4@example.com',
    institution='Institution 4',
    user_type='researcher',
    bio='Bio of user4',
    research_fields={'field1': 'Chemistry', 'field2': 'Organic Chemistry'},
    avatar='avatar4.png',
    published_papers_count=4,
    register_time='2023-04-01 00:00:00',
    status='active',
    uploaded_papers=[paper2],
    favorite_papers=[paper1],
    recent_viewed_papers=[paper1, paper2],
    inbox={'messages': []},
    remarks='Remarks for user4'
)

user5 = create_user(
    username='user5',
    password='password5',
    email='user5@example.com',
    institution='Institution 5',
    user_type='reviewer',
    bio='Bio of user5',
    research_fields={'field1': 'Biology', 'field2': 'Genetics'},
    avatar='avatar5.png',
    published_papers_count=1,
    register_time='2023-05-01 00:00:00',
    status='active',
    uploaded_papers=[paper1],
    favorite_papers=[paper2],
    recent_viewed_papers=[paper1, paper2],
    inbox={'messages': []},
    remarks='Remarks for user5'
)

# 设置用户之间的关注关系
if user1:
    user1.followers.add(user2, user3)
if user2:
    user2.followers.add(user1, user4)
if user3:
    user3.followers.add(user1, user5)
if user4:
    user4.followers.add(user2, user5)
if user5:
    user5.followers.add(user3, user4)

# 创建评论样例数据
comment1 = Comment.objects.create(
    comment_sender=user1,
    paper=paper1,
    likes=10,
    content='This is a comment by user1 on paper1.'
)

comment2 = Comment.objects.create(
    comment_sender=user2,
    paper=paper2,
    likes=5,
    content='This is a comment by user2 on paper2.'
)

comment3 = Comment.objects.create(
    comment_sender=user3,
    paper=paper3,
    likes=8,
    content='This is a comment by user3 on paper3.'
)

comment4 = Comment.objects.create(
    comment_sender=user4,
    paper=paper4,
    likes=12,
    content='This is a comment by user4 on paper4.'
)

comment5 = Comment.objects.create(
    comment_sender=user5,
    paper=paper5,
    likes=7,
    content='This is a comment by user5 on paper5.'
)

# 创建信息样例数据
info1 = Information.objects.create(
    sender=user1,
    receiver=user2,
    title='Information Title 1',
    content='This is the content of information 1.'
)

info2 = Information.objects.create(
    sender=user2,
    receiver=user3,
    title='Information Title 2',
    content='This is the content of information 2.'
)

info3 = Information.objects.create(
    sender=user3,
    receiver=user4,
    title='Information Title 3',
    content='This is the content of information 3.'
)

info4 = Information.objects.create(
    sender=user4,
    receiver=user5,
    title='Information Title 4',
    content='This is the content of information 4.'
)

info5 = Information.objects.create(
    sender=user5,
    receiver=user1,
    title='Information Title 5',
    content='This is the content of information 5.'
)