import { motion } from "motion/react";

export default function Logo() {
  return (
    <div className="relative w-47.5 h-42.5 flex items-center justify-center">
      {/* Stylized Z SVG */}
      <motion.svg
        initial={{ opacity: 0, scale: 0.85 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, ease: [0.2, 0, 0.2, 1] }}
        viewBox="0 0 200 170"
        className="w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Green Gradient for the ribbon arms */}
          <linearGradient id="greenGradientLogoOnly" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#E2FF70" />
            <stop offset="20%" stopColor="#C8EC22" />
            <stop offset="50%" stopColor="#86BE12" />
            <stop offset="80%" stopColor="#409808" />
            <stop offset="100%" stopColor="#1A5204" />
          </linearGradient>

          {/* Dark Gradient for the diagonal */}
          <linearGradient id="darkGradientLogoOnly" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#2A3B5D" />
            <stop offset="50%" stopColor="#162238" />
            <stop offset="100%" stopColor="#0B121E" />
          </linearGradient>

          {/* Pin Yellow Gradient */}
          <linearGradient id="pinGradientLogoOnly" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#FFF550" />
            <stop offset="35%" stopColor="#F0C800" />
            <stop offset="75%" stopColor="#D08C00" />
            <stop offset="100%" stopColor="#A86000" />
          </linearGradient>

          {/* Shadow Filter for depth */}
          <filter id="shadowLogoOnly" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="6" stdDeviation="5" floodOpacity="0.2" />
          </filter>

          {/* Reflection Gradients */}
          <radialGradient id="flareGradientLogoOnly" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#F8C400" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#F8C400" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="pinReflectionLogoOnly" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#E8A000" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#E8A000" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Z Ribbon Structure */}
        <g filter="url(#shadowLogoOnly)">
          {/* Top Arm */}
          <path
            d="M 20,40 C 70,15 135,10 188,20 C 191,21 190,23 182,24 C 125,35 65,55 25,70 Z"
            fill="url(#greenGradientLogoOnly)"
          />
          
          {/* Diagonal Connector */}
          <path
            d="M 182,24 C 110,65 52,115 40,140 C 22,148 20,120 40,102 C 40,100 116,35 188,22 Z"
            fill="url(#greenGradientLogoOnly)"
          />

          {/* Bottom Arm */}
          <path
            d="M 38,126 C 68,127 115,123 134,121 L 134,124 C 98,135 68,140 38,140 C 24,140 24,126 38,126 Z"
            fill="url(#greenGradientLogoOnly)"
          />
        </g>

        {/* Synchronized Reflection under the pin */}
        <motion.g
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 0.7 }}
          transition={{ delay: 0.8, duration: 0.5 }}
          style={{ transformOrigin: '155px 150px' }}
        >
          <motion.g
            animate={{ 
              opacity: [1, 0.3, 1, 0.3, 1], 
              scale: [1, 0.6, 1, 0.6, 1],
              x: [0, -18, 0, 18, 0]
            }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          >
            {/* Horizontal flare */}
            <ellipse cx="155" cy="150" rx="24" ry="2.5" fill="url(#flareGradientLogoOnly)" />
            {/* Downward reflection of the pin tip */}
            <path d="M 147,150 Q 155,166 163,150 Z" fill="url(#pinReflectionLogoOnly)" />
          </motion.g>
        </motion.g>

        {/* Location Pin */}
        <motion.g
          initial={{ y: -50, opacity: 0, scale: 0.5 }}
          animate={{ y: 0, opacity: 1, scale: 0.7 }}
          transition={{ 
            delay: 0.6, 
            type: "spring", 
            stiffness: 240, 
            damping: 18 
          }}
          style={{ transformOrigin: '155px 150px' }}
        >
          {/* Pin Shadow */}
          <motion.ellipse 
            cx="155" cy="150" rx="16" ry="4" fill="black" opacity="0.06"
            animate={{ 
              scale: [1, 0.6, 1, 0.6, 1], 
              opacity: [0.06, 0.01, 0.06, 0.01, 0.06],
              x: [0, -18, 0, 18, 0]
            }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          />
          
          {/* Pin Body */}
          <motion.g
            style={{ transformOrigin: '155px 148px' }}
            animate={{ 
              y: [0, -28, 0, -28, 0],
              x: [0, -18, 0, 18, 0],
              rotate: [0, -8, 0, 8, 0],
              scale: [1, 1.1, 1, 1.1, 1]
            }}
            transition={{ 
              duration: 4, 
              repeat: Infinity, 
              ease: "easeInOut" 
            }}
          >
            {/* Main Pin Shape */}
            <path
              d="M 155,148 C 139,122 123,106 123,86 C 123,68 137,54 155,54 C 173,54 187,68 187,86 C 187,106 171,122 155,148 Z"
              fill="url(#pinGradientLogoOnly)"
              style={{ filter: 'drop-shadow(0px 6px 8px rgba(160, 104, 0, 0.35))' }}
            />
            {/* Inner 3D Highlight */}
            <path
              d="M 155,145 C 141,120 126,105 126,86 C 126,70 139,57 155,57 C 171,57 184,70 184,86 C 184,105 169,120 155,145 Z"
              fill="none"
              stroke="white"
              strokeWidth="1.5"
              opacity="0.35"
            />
            {/* Pin Center Hole */}
            <circle cx="155" cy="86" r="14" fill="white" />
            {/* Inner shadow for the hole */}
            <circle cx="155" cy="86" r="14" fill="none" stroke="rgba(0,0,0,0.08)" strokeWidth="1.5" />
          </motion.g>
        </motion.g>
      </motion.svg>
    </div>
  );
}
