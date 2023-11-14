class AppHolder:
    """
    Utility class to hold the PTB app as a singleton.
    """

    instance_ = None

    @classmethod
    def get_instance(cls):
        return cls.instance_

    @classmethod
    def set_instance(cls, instance):
        cls.instance_ = instance
