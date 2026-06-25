import re

with open('src/config/modelConfig.ts', 'r') as f:
    content = f.read()

# Replace the JSX with React.createElement
bad_jsx = """const ZIcon = ({ size = 24, className = '' }) => (
    <img src={LogoIcon} width={size} height={size} className={className} alt="Z Code" />
);"""

good_ts = """import React from 'react';
const ZIcon = ({ size = 24, className = '' }) => React.createElement('img', { src: LogoIcon, width: size, height: size, className, alt: "Z Code" });"""

content = content.replace(bad_jsx, good_ts)

with open('src/config/modelConfig.ts', 'w') as f:
    f.write(content)

print("Fixed TS error")
