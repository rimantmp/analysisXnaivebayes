class SessionStore:
    def __init__(self):
        self.reset()

    def reset(self):
        self.dataset_id = None
        self.training_id = None
        self.dataset_filename = None
        self.dataset = None
        self.preprocessed = None
        self.excluded_count = 0
        self.extractor = None
        self.matrix = None
        self.top_terms = []
        self.classifier = None
        self.x_train = None
        self.x_test = None
        self.y_train = None
        self.y_test = None
        self.predictions = None
        self.evaluation = None
        self.split = None

    @property
    def step(self):
        if self.evaluation:
            return 6
        if self.classifier:
            return 5
        if self.matrix is not None:
            return 4
        if self.preprocessed is not None:
            return 2
        if self.dataset is not None:
            return 1
        return 0


store = SessionStore()
