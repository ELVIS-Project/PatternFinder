class ParameterValidationError(ValueError):
    def __init__(self, msg, key, arg, valid_options):
        message = msg + "\nParameterValidationException!" + "\n".join([
            "Parameter '{0}' has value {1}".format(key, arg),
            "Valid arguments are: {0}".format(valid_options)])
        super(ParameterValidationException, self).__init__(message)

